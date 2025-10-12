#!/usr/bin/env python3
"""
Golden tests for detector - Compare actual outputs against handcrafted reference plans
"""

import pytest
import json
from pathlib import Path
from detector.detector import run_detector
from detector.schema import plan_to_json


# Directory containing golden test samples
HELL_DIR = Path(__file__).parent.parent / "test_data" / "hell"


@pytest.fixture
def detector_config():
    """Standard detector configuration for golden tests."""
    return {
        'api_base': 'http://127.0.0.1:1234/v1',
        'model': 'test-model',
        'timeout_s': 8,
        'retries': 1,
        'temperature': 0.2,
        'top_p': 0.9,
        'max_context_tokens': 1024,
        'max_output_chars': 2000,
        'json_max_items': 16,
        'max_reason_chars': 64,
        'allow_categories': ['TTS_SPACED', 'UNICODE_STYLIZED', 'CASE_GLITCH', 'SIMPLE_PUNCT'],
        'block_categories': ['STYLE', 'REWRITE', 'MEANING_CHANGE'],
        'max_chunk_size': 600,
        'overlap_size': 50,
        'max_non_alpha_ratio': 0.5,
    }


class StubModelForGolden:
    """Stub model that returns expected golden outputs."""
    
    def __init__(self, expected_plan_path):
        """Load expected plan from JSON file."""
        with open(expected_plan_path, 'r', encoding='utf-8') as f:
            self.expected_plan = json.load(f)
    
    def call_model(self, system_prompt, user_prompt):
        """Return the expected plan as JSON string."""
        return json.dumps(self.expected_plan), ""
    
    def extract_json(self, response):
        """Parse the JSON response."""
        import json
        try:
            parsed = json.loads(response)
            return parsed, ""
        except Exception as e:
            return None, str(e)


class TestGoldenSamples:
    """Test detector against handcrafted reference plans."""
    
    def test_inter_letter_dialogue(self, detector_config):
        """Test inter-letter spacing detection in dialogue."""
        sample_file = HELL_DIR / "inter_letter_dialogue.md"
        plan_file = HELL_DIR / "inter_letter_dialogue.plan.json"
        
        if not sample_file.exists():
            pytest.skip(f"Golden sample not found: {sample_file}")
        
        # Read input text
        with open(sample_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract text nodes (simple line-based for this test)
        nodes = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('#')]
        
        # Create stub with expected plan
        stub = StubModelForGolden(plan_file)
        
        # Import process_text_node to test with stub
        from detector.detector import process_text_node
        
        # Process with stub (combine all nodes for simplicity)
        all_text = " ".join(nodes)
        plan, stats = process_text_node(all_text, detector_config, stub)
        
        # Verify we got some results
        assert len(plan) > 0
        assert stats['suggestions_valid'] > 0
        
        # Check that all expected items are present
        with open(plan_file, 'r', encoding='utf-8') as f:
            expected = json.load(f)
        
        assert len(plan) == len(expected)
    
    def test_unicode_stylized(self, detector_config):
        """Test Unicode stylized character detection."""
        sample_file = HELL_DIR / "unicode_stylized.md"
        plan_file = HELL_DIR / "unicode_stylized.plan.json"
        
        if not sample_file.exists():
            pytest.skip(f"Golden sample not found: {sample_file}")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        nodes = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('#')]
        
        stub = StubModelForGolden(plan_file)
        
        from detector.detector import process_text_node
        all_text = " ".join(nodes)
        plan, stats = process_text_node(all_text, detector_config, stub)
        
        assert len(plan) > 0
        assert stats['suggestions_valid'] > 0
        
        # Verify reasons are correct
        for item in plan:
            assert item.reason == 'UNICODE_STYLIZED'
    
    def test_mixed_problems(self, detector_config):
        """Test mixed problem types in one document."""
        sample_file = HELL_DIR / "mixed_problems.md"
        plan_file = HELL_DIR / "mixed_problems.plan.json"
        
        if not sample_file.exists():
            pytest.skip(f"Golden sample not found: {sample_file}")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        nodes = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('#')]
        
        stub = StubModelForGolden(plan_file)
        
        from detector.detector import process_text_node
        all_text = " ".join(nodes)
        plan, stats = process_text_node(all_text, detector_config, stub)
        
        assert len(plan) > 0
        
        # Check that multiple reason categories are present
        reasons = {item.reason for item in plan}
        assert len(reasons) > 1  # Should have multiple types
        assert 'TTS_SPACED' in reasons
        assert 'UNICODE_STYLIZED' in reasons or 'SIMPLE_PUNCT' in reasons
    
    def test_plan_json_serialization(self, detector_config):
        """Test that plans can be serialized to JSON correctly."""
        sample_file = HELL_DIR / "inter_letter_dialogue.md"
        plan_file = HELL_DIR / "inter_letter_dialogue.plan.json"
        
        if not sample_file.exists():
            pytest.skip(f"Golden sample not found: {sample_file}")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        nodes = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('#')]
        
        stub = StubModelForGolden(plan_file)
        
        from detector.detector import process_text_node
        all_text = " ".join(nodes)
        plan, stats = process_text_node(all_text, detector_config, stub)
        
        # Serialize to JSON-serializable format (returns list, not string)
        json_list = plan_to_json(plan)
        
        # Verify structure
        assert isinstance(json_list, list)
        for item in json_list:
            assert 'find' in item
            assert 'replace' in item
            assert 'reason' in item
            assert isinstance(item['find'], str)
            assert isinstance(item['replace'], str)
            assert isinstance(item['reason'], str)
        
        # Verify it can be JSON-stringified
        import json
        json_str = json.dumps(json_list)
        assert len(json_str) > 0
    
    def test_stable_output(self, detector_config):
        """Test that running detector multiple times produces stable output."""
        sample_file = HELL_DIR / "inter_letter_dialogue.md"
        plan_file = HELL_DIR / "inter_letter_dialogue.plan.json"
        
        if not sample_file.exists():
            pytest.skip(f"Golden sample not found: {sample_file}")
        
        with open(sample_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        nodes = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('#')]
        
        from detector.detector import process_text_node
        all_text = " ".join(nodes)
        
        # Run twice with same stub
        stub1 = StubModelForGolden(plan_file)
        plan1, stats1 = process_text_node(all_text, detector_config, stub1)
        
        stub2 = StubModelForGolden(plan_file)
        plan2, stats2 = process_text_node(all_text, detector_config, stub2)
        
        # Plans should be identical
        assert len(plan1) == len(plan2)
        for item1, item2 in zip(plan1, plan2):
            assert item1.find == item2.find
            assert item1.replace == item2.replace
            assert item1.reason == item2.reason
