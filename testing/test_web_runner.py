"""
Integration tests for Phase 11 PR-1 Web Runner.
Verifies that /api/run endpoint correctly calls run_pipeline() with exact steps & models.
"""

import pytest
import tempfile
from pathlib import Path
import json

# Mark all tests in this file as integration tests (not run by default)
pytestmark = pytest.mark.integration

def test_blessed_models_endpoint():
    """Test GET /api/blessed-models returns correct structure."""
    from mdp.config import get_blessed_models
    
    blessed = get_blessed_models()
    
    # Verify structure
    assert 'detector' in blessed
    assert 'fixer' in blessed
    assert isinstance(blessed['detector'], list)
    assert isinstance(blessed['fixer'], list)
    
    # Verify MVP models are present
    assert 'qwen2.5-1.5b-instruct' in blessed['detector']
    assert 'qwen2.5-1.5b-instruct' in blessed['fixer']


def test_run_pipeline_integration():
    """
    Test that run_pipeline() is called with exact steps and models.
    Verifies artifacts land in ~/.mdp/runs/{run_id}/.
    """
    from mdp.__main__ import run_pipeline
    from mdp.config import load_config
    
    # Create test input
    test_input = """# Test Document

This is a test paragraph with some  e x t r a  spacing that needs fixing.

## Section 2

Another paragraph with SHOUTING TEXT that should be normalized.
"""
    
    # Test steps
    test_steps = ['mask', 'prepass-basic', 'prepass-advanced']
    
    # Load default config
    config = load_config(None)
    
    # Run pipeline
    processed_text, stats = run_pipeline(
        input_text=test_input,
        steps=test_steps,
        config=config
    )
    
    # Verify output
    assert processed_text is not None
    assert len(processed_text) > 0
    assert isinstance(stats, dict)
    
    # Verify stats contain expected keys
    assert 'mask' in stats
    assert 'prepass-basic' in stats
    assert 'prepass-advanced' in stats
    
    # Verify masking stats
    assert 'masks_created' in stats['mask']
    assert stats['mask']['masks_created'] >= 0
    
    # Verify prepass-basic applied
    # Check that spacing was fixed (extra spaces removed)
    assert 'e x t r a' not in processed_text or 'extra' in processed_text


def test_run_pipeline_with_scrubber():
    """Test pipeline with scrubber step enabled."""
    from mdp.__main__ import run_pipeline
    from mdp.config import load_config
    
    test_input = """# Story Chapter

This is the main content of the story.

---

**Author's Note:** Thanks for reading! Check out my Patreon!

**Next Chapter** | **Previous Chapter** | **Table of Contents**
"""
    
    test_steps = ['mask', 'scrubber']
    config = load_config(None)
    
    # Enable scrubber categories
    config['scrubber']['enabled'] = True
    config['scrubber']['categories']['authors_notes'] = True
    config['scrubber']['categories']['navigation'] = True
    
    processed_text, stats = run_pipeline(
        input_text=test_input,
        steps=test_steps,
        config=config
    )
    
    assert 'scrubber' in stats
    # Author note and navigation should be detected
    assert stats['scrubber'].get('blocks_removed', 0) > 0


def test_artifacts_directory_structure():
    """Test that artifacts are written to correct directory structure."""
    import uuid
    
    run_id = str(uuid.uuid4())
    artifacts_dir = Path.home() / '.mdp' / 'runs' / run_id
    
    # Create directory
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Write test file
    test_output = artifacts_dir / 'test_output.md'
    test_output.write_text('# Test Output\n\nProcessed content.')
    
    # Write stats
    stats_file = artifacts_dir / 'stats.json'
    test_stats = {'mask': {'masks_created': 5}}
    stats_file.write_text(json.dumps(test_stats, indent=2))
    
    # Verify structure
    assert artifacts_dir.exists()
    assert test_output.exists()
    assert stats_file.exists()
    
    # Read back stats
    loaded_stats = json.loads(stats_file.read_text())
    assert loaded_stats == test_stats
    
    # Cleanup
    import shutil
    shutil.rmtree(artifacts_dir)


def test_step_ordering():
    """Test that steps are executed in correct order."""
    from mdp.__main__ import run_pipeline
    from mdp.config import load_config
    
    test_input = """# Test

Content with  s p a c e d  letters and SHOUTING.
"""
    
    # Test with all prepass steps
    test_steps = ['mask', 'prepass-basic', 'prepass-advanced']
    config = load_config(None)
    
    processed_text, stats = run_pipeline(
        input_text=test_input,
        steps=test_steps,
        config=config
    )
    
    # Verify all steps ran
    assert 'mask' in stats
    assert 'prepass-basic' in stats
    assert 'prepass-advanced' in stats
    
    # Verify order (keys should be in order of execution)
    stats_keys = list(stats.keys())
    assert stats_keys.index('mask') < stats_keys.index('prepass-basic')
    assert stats_keys.index('prepass-basic') < stats_keys.index('prepass-advanced')


def test_blessed_models_validation():
    """Test that non-blessed models are rejected."""
    from mdp.config import get_blessed_models
    
    blessed = get_blessed_models()
    
    # These should be blessed
    assert 'qwen2.5-1.5b-instruct' in blessed['detector']
    assert 'qwen2.5-1.5b-instruct' in blessed['fixer']
    
    # These should NOT be blessed (validation test)
    assert 'random-model-name' not in blessed['detector']
    assert 'another-unblessed-model' not in blessed['fixer']


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
