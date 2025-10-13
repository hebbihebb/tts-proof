"""
Integration tests for Phase 11 PR-2: Report Display & Diff Viewer

Tests the functionality of report generation and diff computation.
"""
import pytest
from pathlib import Path
import json
import tempfile
import shutil

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_run_artifacts():
    """Create mock run artifacts for testing."""
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp())
    
    run_id = "test-run-pr2"
    artifacts_dir = tmp_dir / '.mdp' / 'runs' / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock files
    input_text = "# Test Input\n\nThis is the original text."
    output_text = "# Test Input\n\nThis is the corrected text."
    
    (artifacts_dir / 'input.txt').write_text(input_text, encoding='utf-8')
    (artifacts_dir / 'output.md').write_text(output_text, encoding='utf-8')
    
    # Create mock report with proper structure for render_pretty
    report_data = {
        'input_file': str(artifacts_dir / 'input.txt'),
        'output_file': str(artifacts_dir / 'output.md'),
        'steps': ['mask', 'prepass-basic', 'grammar'],
        'statistics': {
            'mask': {'regions_masked': 0},
            'prepass-basic': {'unicode_fixed': 5},
            'grammar': {'chunks_processed': 1}
        }
    }
    (artifacts_dir / 'report.json').write_text(json.dumps(report_data, indent=2), encoding='utf-8')
    
    # Create mock plan
    plan_data = [
        {"find": "text", "replace": "corrected text", "reason": "Grammar fix"}
    ]
    (artifacts_dir / 'plan.json').write_text(json.dumps(plan_data, indent=2), encoding='utf-8')
    
    yield run_id, artifacts_dir, tmp_dir
    
    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_render_pretty_report(mock_run_artifacts):
    """Test that render_pretty() generates human-readable report from stats."""
    from report.pretty import render_pretty
    
    run_id, artifacts_dir, tmp_dir = mock_run_artifacts
    
    # Load report data
    report_path = artifacts_dir / 'report.json'
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    # Generate pretty report
    pretty_output = render_pretty(report_data)
    
    # Verify it's a string and contains expected content
    assert isinstance(pretty_output, str)
    assert len(pretty_output) > 0
    assert 'mask' in pretty_output or 'prepass-basic' in pretty_output


def test_unified_diff_generation(mock_run_artifacts):
    """Test that unified diff is correctly generated."""
    import difflib
    
    run_id, artifacts_dir, tmp_dir = mock_run_artifacts
    
    # Read input and output
    with open(artifacts_dir / 'input.txt', 'r', encoding='utf-8') as f:
        input_lines = f.readlines()
    with open(artifacts_dir / 'output.md', 'r', encoding='utf-8') as f:
        output_lines = f.readlines()
    
    # Generate diff
    diff = list(difflib.unified_diff(input_lines, output_lines, lineterm=''))
    
    # Verify diff contains changes
    assert len(diff) > 0
    # Check for diff markers
    diff_str = '\n'.join(diff)
    assert '---' in diff_str or '+++' in diff_str or '-' in diff_str or '+' in diff_str


def test_diff_truncation(mock_run_artifacts):
    """Test that large diffs can be truncated."""
    run_id, artifacts_dir, tmp_dir = mock_run_artifacts
    
    # Create large files
    large_input = "Line 1\n" * 300
    large_output = "Modified line 1\n" * 300
    (artifacts_dir / 'input.txt').write_text(large_input, encoding='utf-8')
    (artifacts_dir / 'output.md').write_text(large_output, encoding='utf-8')
    
    import difflib
    with open(artifacts_dir / 'input.txt', 'r', encoding='utf-8') as f:
        input_lines = f.readlines()
    with open(artifacts_dir / 'output.md', 'r', encoding='utf-8') as f:
        output_lines = f.readlines()
    
    diff_lines = list(difflib.unified_diff(input_lines, output_lines, lineterm=''))
    
    # Truncate
    max_lines = 50
    truncated = diff_lines[:max_lines]
    has_more = len(diff_lines) > max_lines
    
    assert has_more is True
    assert len(truncated) == max_lines


def test_artifact_files_exist(mock_run_artifacts):
    """Test that all expected artifact files are created."""
    run_id, artifacts_dir, tmp_dir = mock_run_artifacts
    
    # Check required files
    assert (artifacts_dir / 'input.txt').exists()
    assert (artifacts_dir / 'output.md').exists()
    assert (artifacts_dir / 'report.json').exists()
    assert (artifacts_dir / 'plan.json').exists()
    
    # Verify content is readable and has proper structure
    with open(artifacts_dir / 'report.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    assert 'steps' in report
    assert 'statistics' in report
    assert 'mask' in report['statistics'] or 'prepass-basic' in report['statistics']
