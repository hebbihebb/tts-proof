#!/usr/bin/env python3
"""
Unit tests for apply/applier.py

Tests edit engine, node grouping, stats tracking, idempotence.
"""

import pytest
from apply.matcher import Match
from apply.applier import (
    apply_matches_to_text,
    apply_matches_to_nodes,
    apply_plan_to_text,
    check_idempotence
)


class TestApplyMatchesToText:
    """Test apply_matches_to_text() function."""
    
    def test_single_match(self):
        """Test applying single match."""
        text = "Hello world"
        matches = [
            Match("world", "WORLD", "test", offset=6, length=5, node_index=0)
        ]
        
        result, stats = apply_matches_to_text(text, matches)
        
        assert result == "Hello WORLD"
        assert stats['replacements_applied'] == 1
        assert stats['length_delta'] == 0  # Same length
    
    def test_multiple_matches(self):
        """Test applying multiple matches in order."""
        text = "the cat and the dog"
        matches = [
            Match("the", "THE", "test", offset=0, length=3, node_index=0),
            Match("the", "THE", "test", offset=12, length=3, node_index=0)
        ]
        
        result, stats = apply_matches_to_text(text, matches)
        
        assert result == "THE cat and THE dog"
        assert stats['replacements_applied'] == 2
    
    def test_length_delta_positive(self):
        """Test length delta calculation for growing text."""
        text = "a b c"
        matches = [
            Match("a", "AAAA", "test", offset=0, length=1, node_index=0),
            Match("b", "BBBB", "test", offset=2, length=1, node_index=0),
            Match("c", "CCCC", "test", offset=4, length=1, node_index=0)
        ]
        
        result, stats = apply_matches_to_text(text, matches)
        
        assert result == "AAAA BBBB CCCC"
        assert stats['length_delta'] == 9  # Added 3 chars to each of 3 words
    
    def test_length_delta_negative(self):
        """Test length delta calculation for shrinking text."""
        text = "AAAA BBBB CCCC"
        matches = [
            Match("AAAA", "A", "test", offset=0, length=4, node_index=0),
            Match("BBBB", "B", "test", offset=5, length=4, node_index=0),
            Match("CCCC", "C", "test", offset=10, length=4, node_index=0)
        ]
        
        result, stats = apply_matches_to_text(text, matches)
        
        assert result == "A B C"
        assert stats['length_delta'] == -9  # Removed 3 chars from each of 3 words
    
    def test_no_matches(self):
        """Test with no matches (text unchanged)."""
        text = "Hello world"
        matches = []
        
        result, stats = apply_matches_to_text(text, matches)
        
        assert result == "Hello world"
        assert stats['replacements_applied'] == 0
        assert stats['length_delta'] == 0
    
    def test_adjacent_matches(self):
        """Test adjacent non-overlapping matches."""
        text = "abcdef"
        matches = [
            Match("abc", "XXX", "test", offset=0, length=3, node_index=0),
            Match("def", "YYY", "test", offset=3, length=3, node_index=0)
        ]
        
        result, stats = apply_matches_to_text(text, matches)
        
        assert result == "XXXYYY"
        assert stats['replacements_applied'] == 2


class TestApplyMatchesToNodes:
    """Test apply_matches_to_nodes() function."""
    
    def test_single_node_single_match(self):
        """Test basic single-node case."""
        text_nodes = ["Hello world"]
        matches = [
            Match("world", "WORLD", "test", offset=6, length=5, node_index=0)
        ]
        
        result_nodes, stats = apply_matches_to_nodes(text_nodes, matches)
        
        assert len(result_nodes) == 1
        assert result_nodes[0] == "Hello WORLD"
        assert stats['nodes_changed'] == 1
        assert stats['replacements_applied'] == 1
    
    def test_multiple_nodes_with_matches(self):
        """Test multiple nodes, each with matches."""
        text_nodes = [
            "First node",
            "Second node",
            "Third node"
        ]
        matches = [
            Match("node", "NODE", "test", offset=6, length=4, node_index=0),
            Match("node", "NODE", "test", offset=7, length=4, node_index=1),
            Match("node", "NODE", "test", offset=6, length=4, node_index=2)
        ]
        
        result_nodes, stats = apply_matches_to_nodes(text_nodes, matches)
        
        assert len(result_nodes) == 3
        assert result_nodes[0] == "First NODE"
        assert result_nodes[1] == "Second NODE"
        assert result_nodes[2] == "Third NODE"
        assert stats['nodes_changed'] == 3
        assert stats['replacements_applied'] == 3
    
    def test_nodes_without_matches_unchanged(self):
        """Test that nodes without matches remain unchanged."""
        text_nodes = [
            "First node",
            "Second node",
            "Third node"
        ]
        matches = [
            Match("node", "NODE", "test", offset=7, length=4, node_index=1)  # Correct offset for "Second node"
        ]
        
        result_nodes, stats = apply_matches_to_nodes(text_nodes, matches)
        
        assert result_nodes[0] == "First node"  # Unchanged
        assert result_nodes[1] == "Second NODE"  # Changed
        assert result_nodes[2] == "Third node"  # Unchanged
        assert stats['nodes_changed'] == 1  # Only one node changed
    
    def test_combined_length_delta(self):
        """Test that length deltas are summed across nodes."""
        text_nodes = ["a", "b", "c"]
        matches = [
            Match("a", "AAAA", "test", offset=0, length=1, node_index=0),
            Match("b", "BBBB", "test", offset=0, length=1, node_index=1),
            Match("c", "CCCC", "test", offset=0, length=1, node_index=2)
        ]
        
        result_nodes, stats = apply_matches_to_nodes(text_nodes, matches)
        
        assert stats['length_delta'] == 9  # 3 chars added per node
        assert stats['nodes_changed'] == 3


class TestApplyPlanToText:
    """Test apply_plan_to_text() function (single-node wrapper)."""
    
    def test_basic_plan_application(self):
        """Test basic plan application."""
        text = "the cat and the dog"
        plan_items = [
            {"find": "the", "replace": "THE", "reason": "capitalize"}
        ]
        
        result, report = apply_plan_to_text(text, plan_items)
        
        assert result == "THE cat and THE dog"
        assert report['replacements_applied'] == 2
        assert report['phase'] == 'apply'
    
    def test_multiple_plan_items(self):
        """Test plan with multiple items."""
        text = "cat dog bird"
        plan_items = [
            {"find": "cat", "replace": "CAT", "reason": "test1"},
            {"find": "dog", "replace": "DOG", "reason": "test2"},
            {"find": "bird", "replace": "BIRD", "reason": "test3"}
        ]
        
        result, report = apply_plan_to_text(text, plan_items)
        
        assert result == "CAT DOG BIRD"
        assert report['replacements_applied'] == 3
        assert report['replacements_skipped_overlap'] == 0
    
    def test_overlapping_items_in_plan(self):
        """Test that overlapping plan items are handled correctly."""
        text = "xxx"
        plan_items = [
            {"find": "xxx", "replace": "LONG", "reason": "long"},
            {"find": "xx", "replace": "SHORT", "reason": "short"}
        ]
        
        result, report = apply_plan_to_text(text, plan_items)
        
        # First occurrence of each pattern found, overlaps removed
        # "xxx" at offset 0 and "xx" at offset 0, 1 - overlap removal should keep longest
        assert "XXX" not in result or "SHORT" not in result  # Can't have both
        assert report['replacements_skipped_overlap'] > 0
    
    def test_no_matches_in_plan(self):
        """Test plan where nothing matches."""
        text = "Hello world"
        plan_items = [
            {"find": "xyz", "replace": "ABC", "reason": "test"}
        ]
        
        result, report = apply_plan_to_text(text, plan_items)
        
        assert result == "Hello world"  # Unchanged
        assert report['replacements_applied'] == 0
        assert report['replacements_skipped_no_match'] == 1
    
    def test_growth_ratio_calculation(self):
        """Test growth ratio calculation."""
        text = "a" * 100  # 100 chars
        plan_items = [
            {"find": "a", "replace": "aa", "reason": "test"}  # Doubles length
        ]
        
        result, report = apply_plan_to_text(text, plan_items)
        
        # All 100 "a"s replaced with "aa" (100 chars added)
        assert report['length_delta'] == 100
        assert report['growth_ratio'] == 1.0  # 100% growth


class TestCheckIdempotence:
    """Test check_idempotence() function."""
    
    def test_idempotent_plan(self):
        """Test plan that is idempotent."""
        text = "the cat and the dog"
        plan_items = [
            {"find": "the", "replace": "THE", "reason": "capitalize"}
        ]
        
        is_idempotent = check_idempotence(text, plan_items)
        
        assert is_idempotent
    
    def test_non_idempotent_plan(self):
        """Test plan that is NOT idempotent (replacement creates new matches)."""
        text = "cat"
        plan_items = [
            {"find": "cat", "replace": "the cat", "reason": "add article"},
            {"find": "the", "replace": "THE", "reason": "capitalize"}
        ]
        
        # First pass: "cat" → "the cat", then "the" → "THE" = "THE cat"
        # Second pass: "THE cat" has "cat" → "the cat" again = "THE the cat"
        # Then "the" → "THE" = "THE THE cat"
        # This demonstrates non-idempotence!
        
        is_idempotent = check_idempotence(text, plan_items)
        
        # This correctly detects non-idempotence
        assert not is_idempotent
    
    def test_empty_plan_idempotent(self):
        """Test that empty plan is trivially idempotent."""
        text = "Hello world"
        plan_items = []
        
        is_idempotent = check_idempotence(text, plan_items)
        
        assert is_idempotent
