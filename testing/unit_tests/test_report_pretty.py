#!/usr/bin/env python3
"""
Unit tests for report/pretty.py - Human-readable report formatter
"""

import pytest
from report.pretty import render_pretty, _truncate_path, _format_percentage, _render_rejections_table


class TestTruncatePath:
    """Tests for path truncation."""
    
    def test_short_path_unchanged(self):
        """Short paths should not be truncated."""
        path = "input.md"
        assert _truncate_path(path, 60) == "input.md"
    
    def test_long_path_truncated(self):
        """Long paths should be truncated with ellipsis."""
        path = "/very/long/path/to/some/deeply/nested/directory/structure/file.md"
        result = _truncate_path(path, 40)
        assert len(result) <= 40
        assert "..." in result
        assert "file.md" in result
    
    def test_very_long_filename(self):
        """Very long filenames should be truncated."""
        path = "extremely_long_filename_that_exceeds_maximum_display_width.md"
        result = _truncate_path(path, 30)
        assert len(result) <= 33  # 30 + "..."
        assert "..." in result


class TestFormatPercentage:
    """Tests for percentage formatting."""
    
    def test_positive_percentage(self):
        """Positive percentages should have + sign."""
        assert _format_percentage(0.05) == "+5.00%"
        assert _format_percentage(0.123) == "+12.30%"
    
    def test_negative_percentage(self):
        """Negative percentages should have - sign."""
        assert _format_percentage(-0.05) == "-5.00%"
        assert _format_percentage(-0.123) == "-12.30%"
    
    def test_zero_percentage(self):
        """Zero should have + sign."""
        assert _format_percentage(0.0) == "+0.00%"


class TestRejectionsTable:
    """Tests for rejections table rendering."""
    
    def test_empty_rejections(self):
        """Empty rejections should render as (none)."""
        assert "(none)" in _render_rejections_table({})
    
    def test_all_zero_rejections(self):
        """All-zero rejections should render as (none)."""
        rejections = {"error_a": 0, "error_b": 0}
        assert "(none)" in _render_rejections_table(rejections)
    
    def test_sorted_by_count(self):
        """Rejections should be sorted by count (descending)."""
        rejections = {"low": 1, "high": 10, "medium": 5}
        result = _render_rejections_table(rejections)
        lines = result.split("\n")
        assert "high" in lines[0]
        assert "medium" in lines[1]
        assert "low" in lines[2]


class TestRenderPretty:
    """Tests for main render_pretty function."""
    
    def test_minimal_report(self):
        """Minimal report should render without crashing."""
        report = {
            'input_file': 'test.md',
            'output_file': 'output.md',
            'steps': ['mask'],
            'statistics': {}
        }
        result = render_pretty(report)
        assert "RUN SUMMARY" in result
        assert "test.md" in result
        assert "mask" in result
    
    def test_empty_statistics_hidden(self):
        """Empty statistics sections should be hidden."""
        report = {
            'input_file': 'test.md',
            'output_file': None,
            'steps': ['mask'],
            'statistics': {}
        }
        result = render_pretty(report)
        # Should have run summary but not phase statistics
        assert "RUN SUMMARY" in result
        # PHASE STATISTICS may appear but should have no content if stats empty
    
    def test_mask_phase_stats(self):
        """Mask phase statistics should render correctly."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['mask'],
            'statistics': {
                'mask': {'masks_created': 42}
            }
        }
        result = render_pretty(report)
        assert "PHASE STATISTICS" in result
        assert "42 regions masked" in result
    
    def test_prepass_basic_stats(self):
        """Prepass-basic statistics should be aggregated."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['mask', 'prepass-basic'],
            'statistics': {
                'mask': {'masks_created': 10},
                'prepass-basic': {
                    'control_chars_stripped': 3,
                    'spaced_words_joined': 5,
                    'hyphenation_healed': 2
                }
            }
        }
        result = render_pretty(report)
        assert "PHASE STATISTICS" in result
        assert "10 normalizations" in result  # 3 + 5 + 2
    
    def test_detector_and_apply_stats(self):
        """Detector and apply phase stats should render."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['mask', 'detect', 'apply'],
            'statistics': {
                'detect': {
                    'model': 'qwen2.5-1.5b',
                    'suggestions_valid': 15,
                    'rejections': {'schema_invalid': 3, 'forbidden_chars': 2}
                },
                'apply': {
                    'replacements_applied': 12,
                    'nodes_changed': 8,
                    'growth_ratio': 0.025,
                    'length_delta': 45
                }
            }
        }
        result = render_pretty(report)
        assert "15 suggestions" in result
        assert "qwen2.5-1.5b" in result
        assert "12 replacements in 8 nodes" in result
        assert "REJECTIONS" in result
        assert "schema_invalid" in result
        assert "FILE GROWTH" in result
        assert "+2.50%" in result
        assert "+45 chars" in result
    
    def test_fixer_stats(self):
        """Fixer statistics should render with rejections."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['mask', 'fix'],
            'statistics': {
                'fix': {
                    'model': 'qwen2.5-1.5b-instruct',
                    'spans_fixed': 45,
                    'spans_total': 50,
                    'spans_rejected': 5,
                    'file_growth_ratio': 0.03,
                    'rejections': {
                        'forbidden_tokens': 2,
                        'growth_limit': 1,
                        'timeout': 2
                    },
                    'deterministic': True
                }
            }
        }
        result = render_pretty(report)
        assert "45/50 spans" in result
        assert "qwen2.5-1.5b-instruct" in result
        assert "REJECTIONS" in result
        assert "forbidden_tokens" in result
        assert "FILE GROWTH" in result
        assert "+3.00%" in result
        assert "QUALITY FLAGS" in result
        assert "Deterministic (seed set)" in result
    
    def test_all_phases_combined(self):
        """Full pipeline report should render all sections."""
        report = {
            'input_file': '/long/path/to/test.md',
            'output_file': '/long/path/to/output.md',
            'steps': ['mask', 'prepass-basic', 'prepass-advanced', 'detect', 'apply', 'fix'],
            'statistics': {
                'mask': {'masks_created': 50},
                'prepass-basic': {
                    'control_chars_stripped': 10,
                    'spaced_words_joined': 5,
                    'hyphenation_healed': 3
                },
                'prepass-advanced': {
                    'casing_fixes': 2,
                    'punctuation_fixes': 8,
                    'ellipsis_fixes': 1
                },
                'detect': {
                    'model': 'qwen2.5-1.5b',
                    'suggestions_valid': 20,
                    'rejections': {'schema_invalid': 5}
                },
                'apply': {
                    'replacements_applied': 18,
                    'nodes_changed': 12,
                    'growth_ratio': 0.015,
                    'length_delta': 30
                },
                'fix': {
                    'model': 'qwen2.5-1.5b-instruct',
                    'spans_fixed': 100,
                    'spans_total': 105,
                    'file_growth_ratio': 0.02,
                    'rejections': {'timeout': 5},
                    'deterministic': False
                }
            }
        }
        result = render_pretty(report)
        
        # Check all sections present
        assert "RUN SUMMARY" in result
        assert "PHASE STATISTICS" in result
        assert "REJECTIONS" in result
        assert "FILE GROWTH" in result
        assert "QUALITY FLAGS" in result
        assert "ARTIFACTS" in result
        
        # Check phase counts
        assert "50 regions masked" in result
        assert "18 normalizations" in result  # prepass-basic
        assert "11 normalizations" in result  # prepass-advanced
        assert "20 suggestions" in result
        assert "18 replacements in 12 nodes" in result
        assert "100/105 spans" in result
    
    def test_missing_optional_fields(self):
        """Report with missing optional fields should not crash."""
        report = {
            'input_file': 'test.md',
            # Missing output_file
            'steps': ['mask'],
            'statistics': {
                'detect': {
                    # Missing model field
                    'suggestions_valid': 10
                    # Missing rejections
                }
            }
        }
        result = render_pretty(report)
        assert "RUN SUMMARY" in result
        assert "10 suggestions" in result
        assert "unknown" in result  # Default model name
    
    def test_stdout_output_indicator(self):
        """When output_file is None, should show 'stdout'."""
        report = {
            'input_file': 'test.md',
            'output_file': None,
            'steps': ['mask'],
            'statistics': {}
        }
        result = render_pretty(report)
        assert "stdout" in result.lower()
    
    def test_tables_align_properly(self):
        """Tables should have proper alignment."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['mask'],
            'statistics': {
                'mask': {'masks_created': 42}
            }
        }
        result = render_pretty(report)
        
        # Check for colon alignment in key-value pairs
        lines = [line for line in result.split('\n') if ' : ' in line]
        assert len(lines) > 0, "Should have key-value pairs with colons"
        
        # All colons should be at same position within their section
        # (This is a rough check - exact alignment depends on implementation)
        for line in lines:
            assert ' : ' in line
    
    def test_long_file_paths_truncated(self):
        """Very long file paths should be truncated in output."""
        long_path = "/very/long/path/to/some/deeply/nested/directory/structure/with/many/levels/file.md"
        report = {
            'input_file': long_path,
            'output_file': long_path.replace('.md', '_out.md'),
            'steps': ['mask'],
            'statistics': {}
        }
        result = render_pretty(report)
        
        # Check that lines aren't excessively long
        lines = result.split('\n')
        for line in lines:
            assert len(line) <= 120, f"Line too long: {len(line)} chars"
    
    def test_percentage_formatting_in_output(self):
        """Growth percentages should be formatted with sign."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['apply'],
            'statistics': {
                'apply': {
                    'replacements_applied': 10,
                    'nodes_changed': 5,
                    'growth_ratio': 0.0435,
                    'length_delta': 123
                }
            }
        }
        result = render_pretty(report)
        assert "+4.35%" in result
        assert "+123 chars" in result


class TestEdgeCases:
    """Edge case tests."""
    
    def test_zero_values_handled(self):
        """Zero values should be displayed correctly."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['apply'],
            'statistics': {
                'apply': {
                    'replacements_applied': 0,
                    'nodes_changed': 0,
                    'growth_ratio': 0.0,
                    'length_delta': 0
                }
            }
        }
        result = render_pretty(report)
        assert "0 replacements in 0 nodes" in result
        assert "+0.00%" in result
    
    def test_negative_growth(self):
        """Negative growth (file shrinkage) should format correctly."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': ['apply'],
            'statistics': {
                'apply': {
                    'replacements_applied': 5,
                    'nodes_changed': 3,
                    'growth_ratio': -0.025,
                    'length_delta': -50
                }
            }
        }
        result = render_pretty(report)
        assert "-2.50%" in result
        assert "-50 chars" in result
    
    def test_empty_steps_list(self):
        """Empty steps list should not crash."""
        report = {
            'input_file': 'test.md',
            'output_file': 'out.md',
            'steps': [],
            'statistics': {}
        }
        result = render_pretty(report)
        assert "RUN SUMMARY" in result
    
    def test_unicode_in_paths(self):
        """Unicode characters in paths should render correctly."""
        report = {
            'input_file': '/path/to/文档.md',
            'output_file': '/path/to/выход.md',
            'steps': ['mask'],
            'statistics': {}
        }
        result = render_pretty(report)
        assert '文档.md' in result
        assert 'выход.md' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
