#!/usr/bin/env python3
"""
Unit tests for detector/schema.py - JSON plan validation
"""

import pytest
from detector.schema import (
    validate_item,
    validate_plan,
    ReplacementItem,
    plan_to_json,
    merge_plans,
    ALLOWED_REASONS,
    FORBIDDEN_REPLACE_CHARS
)


@pytest.fixture
def basic_config():
    """Basic configuration for testing."""
    return {
        'json_max_items': 16,
        'max_output_chars': 2000,
        'max_reason_chars': 64,
        'allow_categories': list(ALLOWED_REASONS),
        'block_categories': ['STYLE', 'REWRITE', 'MEANING_CHANGE'],
    }


class TestItemValidation:
    """Tests for individual item validation."""
    
    def test_valid_item(self, basic_config):
        """Valid item should pass."""
        item = {
            'find': 'F ʟ ᴀ s ʜ',
            'replace': 'Flash',
            'reason': 'TTS_SPACED'
        }
        is_valid, error = validate_item(item, basic_config)
        assert is_valid
        assert error == ''
    
    def test_missing_keys(self, basic_config):
        """Item missing required keys should fail."""
        item = {'find': 'test'}
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        assert 'Missing required keys' in error
    
    def test_empty_find(self, basic_config):
        """Empty 'find' should fail."""
        item = {
            'find': '',
            'replace': 'test',
            'reason': 'TTS_SPACED'
        }
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        assert 'non-empty' in error.lower()
    
    def test_find_too_long(self, basic_config):
        """'find' exceeding 80 chars should fail."""
        item = {
            'find': 'a' * 81,
            'replace': 'test',
            'reason': 'TTS_SPACED'
        }
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        assert '80 chars' in error
    
    def test_find_with_newlines(self, basic_config):
        """'find' with newlines should fail."""
        item = {
            'find': 'test\ntest',
            'replace': 'test',
            'reason': 'TTS_SPACED'
        }
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        assert 'newlines' in error.lower()
    
    def test_forbidden_chars_in_replace(self, basic_config):
        """'replace' with forbidden Markdown chars should fail."""
        forbidden_tests = [
            ('test`code`', '`'),
            ('test*bold*', '*'),
            ('test_italic_', '_'),
            ('test[link]', '['),
            ('test(paren)', '('),
        ]
        
        for replace_text, forbidden_char in forbidden_tests:
            item = {
                'find': 'test',
                'replace': replace_text,
                'reason': 'TTS_SPACED'
            }
            is_valid, error = validate_item(item, basic_config)
            assert not is_valid, f"Should reject '{forbidden_char}'"
            assert 'forbidden' in error.lower()
    
    def test_length_delta_limit(self, basic_config):
        """Length delta exceeding +10 chars should fail."""
        item = {
            'find': 'a',
            'replace': 'a' * 12,  # +11 chars
            'reason': 'TTS_SPACED'
        }
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        assert 'Length delta' in error
    
    def test_invalid_reason(self, basic_config):
        """Reason not in allowed categories should fail."""
        item = {
            'find': 'test',
            'replace': 'test',
            'reason': 'INVALID_REASON'
        }
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        assert 'not in allowed categories' in error
    
    def test_blocked_reason(self, basic_config):
        """Reason in blocked categories should fail."""
        item = {
            'find': 'test',
            'replace': 'test',
            'reason': 'STYLE'
        }
        is_valid, error = validate_item(item, basic_config)
        assert not is_valid
        # Error message says "not in allowed categories" because blocked reasons aren't in allowed list
        assert 'not in allowed' in error or 'is blocked' in error


class TestPlanValidation:
    """Tests for full plan validation."""
    
    def test_valid_plan(self, basic_config):
        """Valid plan should pass."""
        plan = [
            {'find': 'F ʟ ᴀ s ʜ', 'replace': 'Flash', 'reason': 'TTS_SPACED'},
            {'find': 'Bʏ', 'replace': 'By', 'reason': 'UNICODE_STYLIZED'},
        ]
        text_span = 'F ʟ ᴀ s ʜ  and Bʏ text'
        
        valid_items, rejections = validate_plan(plan, text_span, basic_config)
        assert len(valid_items) == 2
        assert all(isinstance(item, ReplacementItem) for item in valid_items)
    
    def test_find_not_in_text(self, basic_config):
        """Items with 'find' not in text should be rejected."""
        plan = [
            {'find': 'notfound', 'replace': 'test', 'reason': 'TTS_SPACED'},
        ]
        text_span = 'some other text'
        
        valid_items, rejections = validate_plan(plan, text_span, basic_config)
        assert len(valid_items) == 0
        assert rejections['no_match'] == 1
    
    def test_duplicate_items(self, basic_config):
        """Duplicate (find, replace) pairs should be rejected."""
        plan = [
            {'find': 'test', 'replace': 'Test', 'reason': 'CASE_GLITCH'},
            {'find': 'test', 'replace': 'Test', 'reason': 'CASE_GLITCH'},
        ]
        text_span = 'test test'
        
        valid_items, rejections = validate_plan(plan, text_span, basic_config)
        assert len(valid_items) == 1
        assert rejections['duplicate'] == 1
    
    def test_budget_limit(self, basic_config):
        """Plans exceeding max items should be truncated."""
        basic_config['json_max_items'] = 2
        plan = [
            {'find': f'test{i}', 'replace': f'Test{i}', 'reason': 'CASE_GLITCH'}
            for i in range(5)
        ]
        text_span = ' '.join(f'test{i}' for i in range(5))
        
        valid_items, rejections = validate_plan(plan, text_span, basic_config)
        assert len(valid_items) <= 2
        assert rejections['budget'] > 0
    
    def test_cumulative_length_delta(self, basic_config):
        """Cumulative length delta exceeding +5% of span should reject entire plan."""
        text_span = 'a' * 100  # 100 chars
        # Max delta is 5% = 5 chars
        plan = [
            {'find': 'a', 'replace': 'aaaa', 'reason': 'TTS_SPACED'},  # +3 chars
            {'find': 'a', 'replace': 'aaa', 'reason': 'TTS_SPACED'},  # +2 chars, total +5 (at limit)
            {'find': 'a', 'replace': 'aa', 'reason': 'TTS_SPACED'},   # +1 char, total +6 (exceeds 5% = 5 chars)
        ]
        
        valid_items, rejections = validate_plan(plan, text_span, basic_config)
        # Entire plan should be rejected due to cumulative delta
        assert len(valid_items) == 0
        assert rejections['length_delta'] > 0


class TestMerging:
    """Tests for plan merging and de-duplication."""
    
    def test_merge_plans(self):
        """Merging should de-duplicate across plans."""
        plan1 = [
            ReplacementItem('test', 'Test', 'CASE_GLITCH'),
            ReplacementItem('foo', 'Foo', 'CASE_GLITCH'),
        ]
        plan2 = [
            ReplacementItem('test', 'Test', 'CASE_GLITCH'),  # Duplicate
            ReplacementItem('bar', 'Bar', 'CASE_GLITCH'),
        ]
        
        merged = merge_plans([plan1, plan2])
        assert len(merged) == 3
        
        # Check de-duplication
        find_replace_pairs = [(item.find, item.replace) for item in merged]
        assert len(find_replace_pairs) == len(set(find_replace_pairs))
    
    def test_plan_to_json(self):
        """plan_to_json should convert items to dict format."""
        items = [
            ReplacementItem('test', 'Test', 'CASE_GLITCH'),
        ]
        
        json_plan = plan_to_json(items)
        assert isinstance(json_plan, list)
        assert len(json_plan) == 1
        assert json_plan[0] == {
            'find': 'test',
            'replace': 'Test',
            'reason': 'CASE_GLITCH'
        }
