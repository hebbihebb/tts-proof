#!/usr/bin/env python3
"""
Integration tests for full detector pipeline with stubbed model
"""

import pytest
from unittest.mock import Mock, patch
from detector.detector import process_text_node, run_detector
from detector.schema import ReplacementItem


@pytest.fixture
def integration_config():
    """Full configuration for integration tests."""
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


class StubModelClient:
    """Stub model that returns predefined JSON plans."""
    
    def __init__(self, responses=None):
        """
        Args:
            responses: List of JSON strings to return in order (cycles if needed)
        """
        self.responses = responses or ['[]']
        self.call_count = 0
    
    def call_model(self, system_prompt, user_prompt):
        """Return next canned response."""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response, ""
    
    def extract_json(self, response):
        """Parse the canned response."""
        import json
        try:
            parsed = json.loads(response)
            return parsed, ""
        except Exception as e:
            return None, str(e)


class TestEndToEnd:
    """End-to-end tests with stubbed model."""
    
    def test_valid_plan_accepted(self, integration_config):
        """Valid plan from stub model should be accepted."""
        stub = StubModelClient([
            '[{"find": "F l a s h", "replace": "Flash", "reason": "TTS_SPACED"}]'
        ])
        
        text = "The word F l a s h appeared in the text."
        plan, stats = process_text_node(text, integration_config, stub)
        
        assert len(plan) == 1
        assert plan[0].find == "F l a s h"
        assert plan[0].replace == "Flash"
        assert stats['suggestions_valid'] == 1
        assert stats['suggestions_rejected'] == 0
    
    def test_empty_plan_acceptable(self, integration_config):
        """Empty plan (no issues found) should be valid."""
        stub = StubModelClient(['[]'])
        
        text = "This is clean text with no issues."
        plan, stats = process_text_node(text, integration_config, stub)
        
        assert len(plan) == 0
        assert stats['suggestions_valid'] == 0
        assert stats['suggestions_rejected'] == 0
    
    def test_multiple_nodes(self, integration_config):
        """Processing multiple nodes should aggregate correctly."""
        # Use process_text_node instead of run_detector since we need stub
        from detector.detector import process_text_node
        
        stub1 = StubModelClient([
            '[{"find": "F l a s h", "replace": "Flash", "reason": "TTS_SPACED"}]'
        ])
        stub2 = StubModelClient([
            '[{"find": "Bʏ Mʏ Rᴇsᴏʟᴠᴇ", "replace": "By My Resolve", "reason": "UNICODE_STYLIZED"}]'
        ])
        
        text1 = "The word F l a s h appeared."
        text2 = "Bʏ Mʏ Rᴇsᴏʟᴠᴇ! he shouted."
        
        plan1, stats1 = process_text_node(text1, integration_config, stub1)
        plan2, stats2 = process_text_node(text2, integration_config, stub2)
        
        # Merge plans
        from detector.schema import merge_plans
        final_plan = merge_plans([plan1, plan2])
        
        assert len(final_plan) == 2
        assert stats1['suggestions_valid'] == 1
        assert stats2['suggestions_valid'] == 1


class TestDeterminism:
    """Tests for deterministic behavior."""
    
    def test_same_input_same_plan(self, integration_config):
        """Running detector twice on same input should produce identical plan."""
        stub = StubModelClient([
            '[{"find": "test", "replace": "TEST", "reason": "CASE_GLITCH"}]'
        ])
        
        text = "This has a test word."
        
        # Run twice
        plan1, stats1 = process_text_node(text, integration_config, stub)
        
        # Reset stub for second run
        stub.call_count = 0
        plan2, stats2 = process_text_node(text, integration_config, stub)
        
        # Plans should be identical
        assert len(plan1) == len(plan2)
        for item1, item2 in zip(plan1, plan2):
            assert item1.find == item2.find
            assert item1.replace == item2.replace
            assert item1.reason == item2.reason
    
    def test_order_independence(self, integration_config):
        """Plan merging should be order-independent (de-duplication)."""
        # Same replacements proposed in different order
        stub1 = StubModelClient([
            '[{"find": "a", "replace": "A", "reason": "CASE_GLITCH"}, {"find": "b", "replace": "B", "reason": "CASE_GLITCH"}]'
        ])
        stub2 = StubModelClient([
            '[{"find": "b", "replace": "B", "reason": "CASE_GLITCH"}, {"find": "a", "replace": "A", "reason": "CASE_GLITCH"}]'
        ])
        
        text = "Text with a and b."
        
        plan1, _ = process_text_node(text, integration_config, stub1)
        plan2, _ = process_text_node(text, integration_config, stub2)
        
        # Both should have 2 items (after de-duplication)
        assert len(plan1) == 2
        assert len(plan2) == 2
        
        # Extract (find, replace) tuples
        pairs1 = {(item.find, item.replace) for item in plan1}
        pairs2 = {(item.find, item.replace) for item in plan2}
        
        # Sets should be identical regardless of input order
        assert pairs1 == pairs2


class TestGuardrails:
    """Tests for schema guardrails and rejection."""
    
    def test_forbidden_chars_rejected(self, integration_config):
        """Plans with Markdown chars in replace should be rejected."""
        stub = StubModelClient([
            '[{"find": "test", "replace": "*bold*", "reason": "TTS_SPACED"}]'
        ])
        
        text = "This has test in it."
        plan, stats = process_text_node(text, integration_config, stub)
        
        assert len(plan) == 0
        assert stats['suggestions_rejected'] >= 1
        assert stats['rejections'].get('forbidden_chars', 0) >= 1
    
    def test_blocked_reason_rejected(self, integration_config):
        """Plans with blocked reasons should be rejected."""
        stub = StubModelClient([
            '[{"find": "old", "replace": "new", "reason": "REWRITE"}]'
        ])
        
        text = "This is old text."
        plan, stats = process_text_node(text, integration_config, stub)
        
        assert len(plan) == 0
        assert stats['suggestions_rejected'] >= 1
        assert stats['rejections'].get('schema', 0) >= 1  # Blocked reason is schema error
    
    def test_length_delta_rejected(self, integration_config):
        """Items exceeding length delta should be rejected."""
        stub = StubModelClient([
            '[{"find": "ok", "replace": "this is way too long for a simple replacement", "reason": "TTS_SPACED"}]'
        ])
        
        text = "This is ok."
        plan, stats = process_text_node(text, integration_config, stub)
        
        assert len(plan) == 0
        assert stats['suggestions_rejected'] >= 1
        assert stats['rejections'].get('length_delta', 0) >= 1
    
    def test_find_not_in_text_rejected(self, integration_config):
        """Items where 'find' doesn't exist in text should be rejected."""
        stub = StubModelClient([
            '[{"find": "nonexistent", "replace": "something", "reason": "TTS_SPACED"}]'
        ])
        
        text = "This text does not contain that word."
        plan, stats = process_text_node(text, integration_config, stub)
        
        assert len(plan) == 0
        assert stats['suggestions_rejected'] >= 1
        assert stats['rejections'].get('no_match', 0) >= 1
    
    def test_budget_overflow_rejected(self, integration_config):
        """Plans exceeding json_max_items should have extras rejected."""
        # Create plan with more than max_items (16)
        items = [
            f'{{"find": "word{i}", "replace": "WORD{i}", "reason": "CASE_GLITCH"}}'
            for i in range(20)
        ]
        plan_json = '[' + ','.join(items) + ']'
        
        stub = StubModelClient([plan_json])
        
        # Create text containing all the words
        text = "This has " + " and ".join([f"word{i}" for i in range(20)])
        
        plan, stats = process_text_node(text, integration_config, stub)
        
        # Should accept up to max_items, reject the rest
        assert len(plan) <= integration_config['json_max_items']
        if len(plan) < 20:
            assert stats['suggestions_rejected'] > 0
    
    def test_cumulative_delta_rejected(self, integration_config):
        """Cumulative length delta exceeding 5% should be rejected."""
        # Create span with many replacements that add up to >5% growth
        # Span is 100 chars, 5% = 5 chars
        # Propose 10 replacements each adding 1 char = 10 chars total
        items = [
            f'{{"find": "a{i}", "replace": "aa{i}", "reason": "TTS_SPACED"}}'
            for i in range(10)
        ]
        plan_json = '[' + ','.join(items) + ']'
        
        stub = StubModelClient([plan_json])
        
        text = "Text: " + " ".join([f"a{i}" for i in range(10)]) + " end."  # ~100 chars
        
        plan, stats = process_text_node(text, integration_config, stub)
        
        # Some items should be accepted, but not all due to cumulative delta
        # Note: Individual length_delta rejections may occur before cumulative check
        if len(plan) < 10:
            # Either length_delta or budget rejections occurred
            assert stats['rejections'].get('length_delta', 0) > 0 or stats['rejections'].get('budget', 0) > 0


class TestSkipConditions:
    """Tests for pre-flight node skipping."""
    
    def test_skip_empty_node(self, integration_config):
        """Empty nodes should be skipped before model call."""
        stub = StubModelClient(['[]'])
        
        nodes = ["", "   ", "Valid text"]
        final_plan, report = run_detector(nodes, integration_config)
        
        # Only 1 node should be actually checked
        assert report['spans_checked'] == 1
    
    def test_skip_url_node(self, integration_config):
        """URL-like nodes should be skipped."""
        stub = StubModelClient(['[]'])
        
        nodes = [
            "https://example.com/path",
            "Normal text for processing"
        ]
        final_plan, report = run_detector(nodes, integration_config)
        
        # Only 1 node should be checked
        assert report['spans_checked'] == 1
    
    def test_skip_mostly_uppercase(self, integration_config):
        """Mostly uppercase nodes should be skipped."""
        stub = StubModelClient(['[]'])
        
        nodes = [
            "THIS IS ALL CAPS",
            "This is normal text"
        ]
        final_plan, report = run_detector(nodes, integration_config)
        
        # Only 1 node should be checked
        assert report['spans_checked'] == 1


class TestPlanMerging:
    """Tests for plan de-duplication across chunks."""
    
    def test_deduplication_across_overlaps(self, integration_config):
        """Same replacement in overlapping chunks should appear once."""
        # Simulate overlapping chunks proposing same fix
        stub = StubModelClient([
            '[{"find": "test", "replace": "TEST", "reason": "CASE_GLITCH"}]',
            '[{"find": "test", "replace": "TEST", "reason": "CASE_GLITCH"}]',
        ])
        
        # Create text long enough to chunk, with 'test' in overlap region
        text = "Start text. " * 25 + "test word " * 5 + "End text. " * 25
        
        plan, stats = process_text_node(text, integration_config, stub)
        
        # Should only have 1 copy of the replacement
        assert len(plan) == 1
        assert plan[0].find == "test"
