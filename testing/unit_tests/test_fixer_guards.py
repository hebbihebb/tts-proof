#!/usr/bin/env python3
"""
Unit tests for fixer/guards.py - Safety validation functions
"""

import pytest
from fixer.guards import (
    check_forbidden_tokens,
    check_length_delta,
    check_is_text,
    validate_output,
    check_file_growth
)


class TestForbiddenTokens:
    """Test forbidden token detection."""
    
    def test_clean_text_passes(self):
        """Plain text without markdown should pass."""
        text = "This is plain text."
        is_valid, error = check_forbidden_tokens(text, text)
        assert is_valid
        assert error == ""
    
    def test_backtick_detected(self):
        """Backticks should be rejected."""
        original = "Clean reference text."
        is_valid, error = check_forbidden_tokens(original, "This has `code` in it.")
        assert not is_valid
        assert "backtick" in error or "`" in error
    
    def test_code_fence_detected(self):
        """Code fences should be rejected."""
        original = "Regular prose without code."
        is_valid, error = check_forbidden_tokens(original, "```python\ncode\n```")
        assert not is_valid
        assert "```" in error
    
    def test_asterisk_detected(self):
        """Asterisks (emphasis/lists) should be rejected."""
        original = "Plain sentence."
        is_valid, error = check_forbidden_tokens(original, "This is *emphasized* text.")
        assert not is_valid
        assert "*" in error
    
    def test_link_syntax_detected(self):
        """Link syntax should be rejected."""
        original = "Nothing fancy here."
        is_valid, error = check_forbidden_tokens(original, "Check [this link](http://example.com)")
        assert not is_valid
        assert "[" in error or "]" in error or "(" in error
    
    def test_url_detected(self):
        """URLs should be rejected."""
        original = "Simple statement."
        is_valid, error = check_forbidden_tokens(original, "Visit http://example.com")
        assert not is_valid
        assert "http" in error.lower()
    
    def test_html_detected(self):
        """HTML tags should be rejected."""
        original = "Plain vanilla text."
        is_valid, error = check_forbidden_tokens(original, "This has <strong>HTML</strong>")
        assert not is_valid
        assert "<" in error or ">" in error


class TestLengthDelta:
    """Test length growth/shrinkage limits."""
    
    def test_no_change_passes(self):
        """Identical length should pass."""
        is_valid, error = check_length_delta("hello world", "hello world", 0.20)
        assert is_valid
    
    def test_small_growth_passes(self):
        """Growth under limit should pass."""
        original = "hello world"
        output = "hello world!"  # ~9% growth
        is_valid, error = check_length_delta(original, output, 0.20)  # Allow 20%
        assert is_valid
    
    def test_excessive_growth_rejected(self):
        """Growth over limit should be rejected."""
        original = "hello"
        output = "hello world extra text"  # >100% growth
        is_valid, error = check_length_delta(original, output, 0.50)  # Allow only 50%
        assert not is_valid
        assert "growth" in error.lower()
    
    def test_moderate_shrinkage_allowed(self):
        """Moderate shrinkage (< 50%) should pass."""
        original = "hello world extra"
        output = "hello world"  # ~33% shrinkage
        is_valid, error = check_length_delta(original, output, 0.20)
        assert is_valid
    
    def test_excessive_shrinkage_rejected(self):
        """Excessive shrinkage (> 50%) should be rejected."""
        original = "hello world extra text more"
        output = "hi"  # >50% shrinkage
        is_valid, error = check_length_delta(original, output, 0.20)
        assert not is_valid
        assert "shrinkage" in error.lower()
    
    def test_empty_input_edge_case(self):
        """Empty input with non-empty output should be rejected."""
        is_valid, error = check_length_delta("", "hello", 0.20)
        assert not is_valid


class TestIsText:
    """Test text validation."""
    
    def test_normal_text_passes(self):
        """Normal text should pass."""
        is_valid, error = check_is_text("This is normal text.")
        assert is_valid
    
    def test_empty_string_rejected(self):
        """Empty string should be rejected."""
        is_valid, error = check_is_text("")
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_whitespace_only_rejected(self):
        """Whitespace-only should be rejected."""
        is_valid, error = check_is_text("   \n\t  ")
        assert not is_valid
        assert "whitespace" in error.lower()
    
    def test_single_word_passes(self):
        """Single word should pass."""
        is_valid, error = check_is_text("hello")
        assert is_valid


class TestValidateOutput:
    """Test combined validation function."""
    
    def test_valid_output_passes(self):
        """Clean output should pass all checks."""
        original = "This has minor issues."
        output = "This has minor issues!"
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20
        }
        
        is_valid, result, reason = validate_output(original, output, config)
        assert is_valid
        assert result == output.strip()
        assert reason == ""
    
    def test_forbidden_token_rejected(self):
        """Output with markdown should be rejected."""
        original = "This is text."
        output = "This is `code`."
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20
        }
        
        is_valid, result, reason = validate_output(original, output, config)
        assert not is_valid
        assert result == original  # Fail-safe to original
        assert reason == "forbidden_tokens"
    
    def test_excessive_growth_rejected(self):
        """Output with excessive growth should be rejected."""
        original = "Short."
        output = "This is a much longer sentence with lots of extra words."
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20
        }
        
        is_valid, result, reason = validate_output(original, output, config)
        assert not is_valid
        assert result == original
        assert reason == "growth_limit"
    
    def test_empty_output_rejected(self):
        """Empty output should be rejected."""
        original = "This is text."
        output = ""
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20
        }
        
        is_valid, result, reason = validate_output(original, output, config)
        assert not is_valid
        assert result == original
        assert reason == "empty_or_non_text"
    
    def test_whitespace_trimmed(self):
        """Output whitespace should be trimmed."""
        original = "This is text."
        output = "  This is text.  \n"
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20
        }
        
        is_valid, result, reason = validate_output(original, output, config)
        assert is_valid
        assert result == "This is text."
    
    def test_markdown_tokens_can_be_disabled(self):
        """Forbidden token check can be disabled via config."""
        original = "This is text."
        output = "This is `code`."
        config = {
            'forbid_markdown_tokens': False,  # Disabled
            'node_max_growth_ratio': 0.20
        }
        
        is_valid, result, reason = validate_output(original, output, config)
        assert is_valid  # Should pass since check is disabled


class TestFileGrowth:
    """Test file-level growth checking."""
    
    def test_no_growth(self):
        """Identical file should pass."""
        is_valid, ratio = check_file_growth("hello world", "hello world", 0.05)
        assert is_valid
        assert ratio == 0.0
    
    def test_small_growth_passes(self):
        """Small growth under limit should pass."""
        original = "a" * 1000
        fixed = "a" * 1040  # 4% growth
        is_valid, ratio = check_file_growth(original, fixed, 0.05)
        assert is_valid
        assert 0.03 < ratio < 0.05
    
    def test_excessive_growth_rejected(self):
        """Growth over limit should be rejected."""
        original = "a" * 1000
        fixed = "a" * 1100  # 10% growth
        is_valid, ratio = check_file_growth(original, fixed, 0.05)
        assert not is_valid
        assert ratio > 0.05
    
    def test_shrinkage_within_limit_passes(self):
        """Small shrinkage should pass."""
        original = "a" * 1000
        fixed = "a" * 960  # 4% shrinkage
        is_valid, ratio = check_file_growth(original, fixed, 0.05)
        assert is_valid
        assert -0.05 < ratio < 0.0
    
    def test_empty_input_edge_case(self):
        """Empty input should pass."""
        is_valid, ratio = check_file_growth("", "", 0.05)
        assert is_valid
        assert ratio == 0.0
