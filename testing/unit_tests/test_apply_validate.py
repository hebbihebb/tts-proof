#!/usr/bin/env python3
"""
Unit tests for apply/validate.py

Tests 7 structural validators individually and validate_all integration.
"""

import pytest
from apply.validate import (
    validate_mask_parity,
    validate_backtick_parity,
    validate_bracket_balance,
    validate_link_sanity,
    validate_fence_parity,
    validate_no_new_markdown_tokens,
    validate_length_delta_budget,
    validate_all
)


class TestValidateMaskParity:
    """Test validate_mask_parity() function."""
    
    def test_no_masks_valid(self):
        """Test when neither original nor edited have masks."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_mask_parity(original, edited)
        
        assert is_valid
        assert error == ""
    
    def test_same_masks_valid(self):
        """Test when both have same masks."""
        original = "Hello __MASKED_0__ world __MASKED_1__"
        edited = "HELLO __MASKED_0__ WORLD __MASKED_1__"
        
        is_valid, error = validate_mask_parity(original, edited)
        
        assert is_valid
    
    def test_different_count_invalid(self):
        """Test when mask counts differ."""
        original = "Hello __MASKED_0__ world"
        edited = "HELLO world"  # Missing mask
        
        is_valid, error = validate_mask_parity(original, edited)
        
        assert not is_valid
        assert "1 masks in original, 0 in edited" in error
    
    def test_different_mask_ids_invalid(self):
        """Test when mask IDs change."""
        original = "Hello __MASKED_0__ world"
        edited = "Hello __MASKED_1__ world"  # Different mask ID
        
        is_valid, error = validate_mask_parity(original, edited)
        
        assert not is_valid
        assert "individual mask counts changed" in error
    
    def test_multiple_same_masks_valid(self):
        """Test when same mask appears multiple times."""
        original = "__MASKED_0__ text __MASKED_0__ more __MASKED_0__"
        edited = "__MASKED_0__ TEXT __MASKED_0__ MORE __MASKED_0__"
        
        is_valid, error = validate_mask_parity(original, edited)
        
        assert is_valid


class TestValidateBacktickParity:
    """Test validate_backtick_parity() function."""
    
    def test_no_backticks_valid(self):
        """Test when no backticks in either."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_backtick_parity(original, edited)
        
        assert is_valid
    
    def test_same_count_valid(self):
        """Test when backtick counts match."""
        original = "Use `code` here and `there`"
        edited = "Use `CODE` here and `THERE`"
        
        is_valid, error = validate_backtick_parity(original, edited)
        
        assert is_valid
    
    def test_different_count_invalid(self):
        """Test when backtick count changes."""
        original = "Use `code` here"
        edited = "Use code here"  # Missing backticks
        
        is_valid, error = validate_backtick_parity(original, edited)
        
        assert not is_valid
        assert "2 in original, 0 in edited" in error
    
    def test_code_fence_backticks(self):
        """Test with code fence (triple backticks)."""
        original = "```\ncode\n```"
        edited = "```\nCODE\n```"
        
        is_valid, error = validate_backtick_parity(original, edited)
        
        assert is_valid  # 6 backticks in both


class TestValidateBracketBalance:
    """Test validate_bracket_balance() function."""
    
    def test_no_brackets_valid(self):
        """Test when no brackets."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_bracket_balance(original, edited)
        
        assert is_valid
    
    def test_balanced_brackets_valid(self):
        """Test when brackets remain balanced."""
        original = "[link](url) and {json: [array]}"
        edited = "[LINK](URL) and {JSON: [ARRAY]}"
        
        is_valid, error = validate_bracket_balance(original, edited)
        
        assert is_valid
    
    def test_bracket_count_changed_invalid(self):
        """Test when bracket count changes."""
        original = "[link](url)"
        edited = "link(url)"  # Missing [
        
        is_valid, error = validate_bracket_balance(original, edited)
        
        assert not is_valid
        assert "[ count changed" in error
    
    def test_unbalanced_after_edit_invalid(self):
        """Test when edit creates imbalance."""
        original = "test"
        edited = "test ("  # Unbalanced paren
        
        is_valid, error = validate_bracket_balance(original, edited)
        
        assert not is_valid
        assert "became unbalanced" in error
    
    def test_multiple_bracket_types(self):
        """Test with multiple bracket types."""
        original = "array[0] and map{key} and func()"
        edited = "ARRAY[0] and MAP{KEY} and FUNC()"
        
        is_valid, error = validate_bracket_balance(original, edited)
        
        assert is_valid


class TestValidateLinkSanity:
    """Test validate_link_sanity() function."""
    
    def test_no_links_valid(self):
        """Test when no links."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_link_sanity(original, edited)
        
        assert is_valid
    
    def test_same_link_count_valid(self):
        """Test when link count unchanged."""
        original = "[link1](url1) and [link2](url2)"
        edited = "[LINK1](URL1) and [LINK2](URL2)"
        
        is_valid, error = validate_link_sanity(original, edited)
        
        assert is_valid
    
    def test_link_count_changed_invalid(self):
        """Test when link count changes."""
        original = "[link](url)"
        edited = "link url"  # Missing ]( pair
        
        is_valid, error = validate_link_sanity(original, edited)
        
        assert not is_valid
        assert "]( count changed from 1 to 0" in error


class TestValidateFenceParity:
    """Test validate_fence_parity() function."""
    
    def test_no_fences_valid(self):
        """Test when no fences."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_fence_parity(original, edited)
        
        assert is_valid
    
    def test_even_fences_valid(self):
        """Test when fence count remains even."""
        original = "```\ncode\n```"
        edited = "```\nCODE\n```"
        
        is_valid, error = validate_fence_parity(original, edited)
        
        assert is_valid
    
    def test_fence_count_changed_invalid(self):
        """Test when fence count changes."""
        original = "```\ncode\n```"
        edited = "code"  # Missing fences
        
        is_valid, error = validate_fence_parity(original, edited)
        
        assert not is_valid
        assert "``` count changed from 2 to 0" in error
    
    def test_odd_fences_invalid(self):
        """Test when fence count becomes odd."""
        original = "text"
        edited = "``` text"  # Odd fence count
        
        is_valid, error = validate_fence_parity(original, edited)
        
        assert not is_valid
        assert "``` count changed from 0 to 1" in error  # Catches count change first


class TestValidateNoNewMarkdownTokens:
    """Test validate_no_new_markdown_tokens() function."""
    
    def test_no_tokens_added_valid(self):
        """Test when no new tokens added."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_no_new_markdown_tokens(original, edited)
        
        assert is_valid
    
    def test_same_tokens_valid(self):
        """Test when tokens preserved."""
        original = "*italic* **bold** `code` [link](url)"
        edited = "*ITALIC* **BOLD** `CODE` [LINK](URL)"
        
        is_valid, error = validate_no_new_markdown_tokens(original, edited)
        
        assert is_valid
    
    def test_new_asterisk_invalid(self):
        """Test when new asterisk added."""
        original = "text"
        edited = "*text*"  # Added 2 asterisks
        
        is_valid, error = validate_no_new_markdown_tokens(original, edited)
        
        assert not is_valid
        assert "'*' increased from 0 to 2" in error
    
    def test_new_backtick_invalid(self):
        """Test when new backtick added."""
        original = "code"
        edited = "`code`"
        
        is_valid, error = validate_no_new_markdown_tokens(original, edited)
        
        assert not is_valid
        assert "'`' increased from 0 to 2" in error
    
    def test_new_bracket_invalid(self):
        """Test when new bracket added."""
        original = "link"
        edited = "[link]"
        
        is_valid, error = validate_no_new_markdown_tokens(original, edited)
        
        assert not is_valid
        assert "'[' increased" in error or "']' increased" in error
    
    def test_removed_tokens_valid(self):
        """Test that removing tokens is allowed."""
        original = "*italic*"
        edited = "italic"  # Removed asterisks - should be valid
        
        is_valid, error = validate_no_new_markdown_tokens(original, edited)
        
        assert is_valid  # Removing is OK, only adding is forbidden


class TestValidateLengthDeltaBudget:
    """Test validate_length_delta_budget() function."""
    
    def test_no_change_valid(self):
        """Test when length unchanged."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        is_valid, error = validate_length_delta_budget(original, edited)
        
        assert is_valid
    
    def test_within_budget_valid(self):
        """Test when growth within 1% budget."""
        original = "a" * 1000  # 1000 chars
        edited = "a" * 1010  # 1010 chars (1% growth)
        
        is_valid, error = validate_length_delta_budget(original, edited, max_ratio=0.01)
        
        assert is_valid
    
    def test_shrinking_valid(self):
        """Test that shrinking is always valid."""
        original = "a" * 1000
        edited = "a" * 500  # 50% shrinkage
        
        is_valid, error = validate_length_delta_budget(original, edited)
        
        assert is_valid
    
    def test_exceeds_budget_invalid(self):
        """Test when growth exceeds budget."""
        original = "a" * 100  # 100 chars
        edited = "a" * 150  # 150 chars (50% growth, exceeds 1%)
        
        is_valid, error = validate_length_delta_budget(original, edited, max_ratio=0.01)
        
        assert not is_valid
        assert "50.00% growth" in error
        assert "max 1.00%" in error
    
    def test_custom_budget(self):
        """Test with custom budget."""
        original = "a" * 100
        edited = "a" * 150  # 50% growth
        
        is_valid, error = validate_length_delta_budget(original, edited, max_ratio=0.5)
        
        assert is_valid  # Within 50% budget
    
    def test_empty_original_valid(self):
        """Test with empty original (any growth allowed)."""
        original = ""
        edited = "a" * 1000
        
        is_valid, error = validate_length_delta_budget(original, edited)
        
        assert is_valid  # Empty file exception


class TestValidateAll:
    """Test validate_all() integration function."""
    
    def test_all_pass(self):
        """Test when all validators pass."""
        original = "Hello world"
        edited = "HELLO WORLD"
        
        all_passed, failures = validate_all(original, edited)
        
        assert all_passed
        assert len(failures) == 0
    
    def test_single_failure(self):
        """Test when one validator fails."""
        original = "text"
        edited = "te*t"  # New markdown token, same length
        
        all_passed, failures = validate_all(original, edited)
        
        assert not all_passed
        assert len(failures) == 1
        assert "Markdown Token Guard" in failures[0]
    
    def test_multiple_failures(self):
        """Test when multiple validators fail."""
        original = "text"
        edited = "*`[text](`*"  # Multiple new tokens, unbalanced
        
        all_passed, failures = validate_all(original, edited)
        
        assert not all_passed
        assert len(failures) >= 2  # At least token guard and balance
    
    def test_mask_parity_failure(self):
        """Test mask parity failure."""
        original = "__MASKED_0__ text"
        edited = "text"  # Missing mask
        
        all_passed, failures = validate_all(original, edited)
        
        assert not all_passed
        assert any("Mask Parity" in f for f in failures)
    
    def test_length_delta_failure(self):
        """Test length delta budget failure."""
        original = "a" * 100
        edited = "a" * 200  # 100% growth
        config = {'apply': {'max_file_growth_ratio': 0.01}}
        
        all_passed, failures = validate_all(original, edited, config)
        
        assert not all_passed
        assert any("Length Delta Budget" in f for f in failures)
    
    def test_config_overrides(self):
        """Test that config overrides work."""
        original = "a" * 100
        edited = "a" * 150  # 50% growth
        
        # With default 1% budget - should fail
        all_passed_default, _ = validate_all(original, edited)
        assert not all_passed_default
        
        # With custom 50% budget - should pass
        config = {'apply': {'max_file_growth_ratio': 0.5}}
        all_passed_custom, _ = validate_all(original, edited, config)
        assert all_passed_custom
