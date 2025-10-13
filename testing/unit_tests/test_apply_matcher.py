#!/usr/bin/env python3
"""
Unit tests for apply/matcher.py

Tests literal matching, all occurrences, overlap prevention, maximal munch.
"""

import pytest
from apply.matcher import (
    Match,
    find_all_matches,
    find_matches_in_nodes,
    remove_overlapping_matches,
    validate_no_masked_edits
)


class TestMatchDataclass:
    """Test Match dataclass and helper methods."""
    
    def test_match_end_offset(self):
        """Test Match.end_offset() calculation."""
        match = Match(
            find="test",
            replace="replacement",
            reason="testing",
            offset=10,
            length=4,
            node_index=0
        )
        assert match.end_offset() == 14
    
    def test_match_overlaps_true(self):
        """Test Match.overlaps() when matches overlap."""
        match1 = Match("abc", "xyz", "reason", offset=10, length=3, node_index=0)
        match2 = Match("bcd", "yzw", "reason", offset=12, length=3, node_index=0)
        
        assert match1.overlaps(match2)
        assert match2.overlaps(match1)
    
    def test_match_overlaps_false_separate(self):
        """Test Match.overlaps() when matches are separate."""
        match1 = Match("abc", "xyz", "reason", offset=10, length=3, node_index=0)
        match2 = Match("def", "uvw", "reason", offset=20, length=3, node_index=0)
        
        assert not match1.overlaps(match2)
        assert not match2.overlaps(match1)
    
    def test_match_overlaps_false_adjacent(self):
        """Test Match.overlaps() when matches are adjacent but not overlapping."""
        match1 = Match("abc", "xyz", "reason", offset=10, length=3, node_index=0)
        match2 = Match("def", "uvw", "reason", offset=13, length=3, node_index=0)
        
        assert not match1.overlaps(match2)
        assert not match2.overlaps(match1)


class TestFindAllMatches:
    """Test find_all_matches() function."""
    
    def test_single_occurrence(self):
        """Test finding single occurrence."""
        text = "Hello world"
        matches = find_all_matches(text, "world", "WORLD", "test", node_index=0)
        
        assert len(matches) == 1
        assert matches[0].find == "world"
        assert matches[0].replace == "WORLD"
        assert matches[0].offset == 6
        assert matches[0].length == 5
    
    def test_multiple_occurrences_non_overlapping(self):
        """Test finding all non-overlapping occurrences."""
        text = "the cat and the dog and the bird"
        matches = find_all_matches(text, "the", "THE", "test", node_index=0)
        
        assert len(matches) == 3
        assert matches[0].offset == 0
        assert matches[1].offset == 12
        assert matches[2].offset == 24
    
    def test_no_matches(self):
        """Test when pattern not found."""
        text = "Hello world"
        matches = find_all_matches(text, "xyz", "ABC", "test", node_index=0)
        
        assert len(matches) == 0
    
    def test_overlapping_prevented_by_search_start(self):
        """Test that search_start advancement prevents overlapping matches."""
        text = "aaa"
        matches = find_all_matches(text, "aa", "XX", "test", node_index=0)
        
        # Should only find first "aa", not overlapping second one
        assert len(matches) == 1
        assert matches[0].offset == 0
    
    def test_case_sensitive(self):
        """Test that matching is case-sensitive."""
        text = "Hello HELLO hello"
        matches = find_all_matches(text, "hello", "HI", "test", node_index=0)
        
        # Should only match lowercase "hello"
        assert len(matches) == 1
        assert matches[0].offset == 12


class TestFindMatchesInNodes:
    """Test find_matches_in_nodes() function."""
    
    def test_single_node_single_item(self):
        """Test basic single-node, single-item case."""
        text_nodes = ["Hello world"]
        plan_items = [{"find": "world", "replace": "WORLD", "reason": "test"}]
        
        matches = find_matches_in_nodes(text_nodes, plan_items)
        
        assert len(matches) == 1
        assert matches[0].node_index == 0
        assert matches[0].offset == 6
    
    def test_multiple_nodes(self):
        """Test matching across multiple nodes."""
        text_nodes = ["First node", "Second node", "Third node"]
        plan_items = [{"find": "node", "replace": "NODE", "reason": "test"}]
        
        matches = find_matches_in_nodes(text_nodes, plan_items)
        
        assert len(matches) == 3
        assert matches[0].node_index == 0
        assert matches[1].node_index == 1
        assert matches[2].node_index == 2
    
    def test_multiple_plan_items(self):
        """Test multiple plan items."""
        text_nodes = ["cat dog bird"]
        plan_items = [
            {"find": "cat", "replace": "CAT", "reason": "test1"},
            {"find": "dog", "replace": "DOG", "reason": "test2"},
            {"find": "bird", "replace": "BIRD", "reason": "test3"}
        ]
        
        matches = find_matches_in_nodes(text_nodes, plan_items)
        
        assert len(matches) == 3
    
    def test_sorting_by_node_offset_length(self):
        """Test that matches are sorted by (node_index, offset, -length)."""
        text_nodes = ["xx xxx xxxx"]
        plan_items = [
            {"find": "xx", "replace": "A", "reason": "short"},
            {"find": "xxx", "replace": "B", "reason": "medium"},
            {"find": "xxxx", "replace": "C", "reason": "long"}
        ]
        
        matches = find_matches_in_nodes(text_nodes, plan_items)
        
        # find_all_matches finds ALL non-overlapping occurrences of EACH pattern
        # "xx" pattern finds: offset 0, 3, 7, 9
        # "xxx" pattern finds: offset 3, 7
        # "xxxx" pattern finds: offset 7
        # Total 7 matches, many overlapping
        
        # After sorting by (node, offset, -length), at each offset longest is first
        # At offset 0: length 2
        # At offset 3: lengths 3, 2 → 3 first
        # At offset 7: lengths 4, 3, 2 → 4 first
        # At offset 9: length 2
        
        assert len(matches) == 7  # Before de-duplication
        
        # Check that at offset 3, xxx (length 3) comes before xx (length 2)
        offset_3_matches = [m for m in matches if m.offset == 3]
        assert len(offset_3_matches) == 2
        assert offset_3_matches[0].length == 3  # xxx first
        assert offset_3_matches[1].length == 2  # xx second
        
        # Check that at offset 7, xxxx (length 4) comes first
        offset_7_matches = [m for m in matches if m.offset == 7]
        assert len(offset_7_matches) == 3
        assert offset_7_matches[0].length == 4  # xxxx first
        assert offset_7_matches[1].length == 3  # xxx second
        assert offset_7_matches[2].length == 2  # xx third
    
    def test_empty_nodes(self):
        """Test with empty node list."""
        text_nodes = []
        plan_items = [{"find": "test", "replace": "TEST", "reason": "test"}]
        
        matches = find_matches_in_nodes(text_nodes, plan_items)
        
        assert len(matches) == 0
    
    def test_empty_plan(self):
        """Test with empty plan list."""
        text_nodes = ["test text"]
        plan_items = []
        
        matches = find_matches_in_nodes(text_nodes, plan_items)
        
        assert len(matches) == 0


class TestRemoveOverlappingMatches:
    """Test remove_overlapping_matches() function."""
    
    def test_no_overlaps(self):
        """Test when matches don't overlap."""
        matches = [
            Match("a", "A", "r1", offset=0, length=1, node_index=0),
            Match("b", "B", "r2", offset=5, length=1, node_index=0),
            Match("c", "C", "r3", offset=10, length=1, node_index=0)
        ]
        
        non_overlapping, count = remove_overlapping_matches(matches)
        
        assert len(non_overlapping) == 3
        assert count == 0
    
    def test_simple_overlap_keeps_first(self):
        """Test that first match is kept when overlaps occur."""
        matches = [
            Match("abc", "A", "r1", offset=0, length=3, node_index=0),
            Match("bcd", "B", "r2", offset=1, length=3, node_index=0),
        ]
        
        non_overlapping, count = remove_overlapping_matches(matches)
        
        assert len(non_overlapping) == 1
        assert non_overlapping[0].find == "abc"  # First match kept
        assert count == 1
    
    def test_maximal_munch_via_sort_order(self):
        """Test that longest match is kept due to sort order (maximal munch)."""
        # Matches should be pre-sorted by (node_index, offset, -length)
        matches = [
            Match("xxxx", "LONG", "r1", offset=0, length=4, node_index=0),  # Longest first
            Match("xxx", "MED", "r2", offset=0, length=3, node_index=0),
            Match("xx", "SHORT", "r3", offset=0, length=2, node_index=0)
        ]
        
        non_overlapping, count = remove_overlapping_matches(matches)
        
        assert len(non_overlapping) == 1
        assert non_overlapping[0].find == "xxxx"  # Longest kept
        assert count == 2
    
    def test_different_nodes_no_overlap(self):
        """Test that matches in different nodes don't interfere."""
        matches = [
            Match("a", "A", "r1", offset=0, length=1, node_index=0),
            Match("a", "A", "r2", offset=0, length=1, node_index=1),
            Match("a", "A", "r3", offset=0, length=1, node_index=2)
        ]
        
        non_overlapping, count = remove_overlapping_matches(matches)
        
        assert len(non_overlapping) == 3  # All kept, different nodes
        assert count == 0


class TestValidateNoMaskedEdits:
    """Test validate_no_masked_edits() function."""
    
    def test_no_masks_all_valid(self):
        """Test when there are no masks."""
        text = "Hello world"
        matches = [
            Match("world", "WORLD", "r1", offset=6, length=5, node_index=0)
        ]
        mask_ranges = []
        
        is_valid, error = validate_no_masked_edits(matches, text, mask_ranges)
        
        assert is_valid
        assert error == ""
    
    def test_match_outside_mask(self):
        """Test match outside masked region."""
        text = "Hello __MASKED_0__ world"
        matches = [
            Match("Hello", "HI", "r1", offset=0, length=5, node_index=0),
            Match("world", "WORLD", "r2", offset=19, length=5, node_index=0)
        ]
        mask_ranges = [(6, 18)]  # __MASKED_0__ range
        
        is_valid, error = validate_no_masked_edits(matches, text, mask_ranges)
        
        assert is_valid
        assert error == ""
    
    def test_match_inside_mask_rejected(self):
        """Test that match inside masked region is rejected."""
        text = "Hello __MASKED_0__ world"
        matches = [
            Match("MASKED", "UNMASKED", "r1", offset=8, length=6, node_index=0)
        ]
        mask_ranges = [(6, 18)]
        
        is_valid, error = validate_no_masked_edits(matches, text, mask_ranges)
        
        assert not is_valid
        assert "masked region" in error.lower()
    
    def test_match_overlaps_mask_start(self):
        """Test match that overlaps with mask start."""
        text = "Hello __MASKED_0__ world"
        matches = [
            Match("o __", "O_", "r1", offset=4, length=4, node_index=0)
        ]
        mask_ranges = [(6, 18)]
        
        is_valid, error = validate_no_masked_edits(matches, text, mask_ranges)
        
        assert not is_valid
    
    def test_match_overlaps_mask_end(self):
        """Test match that overlaps with mask end."""
        text = "Hello __MASKED_0__ world"
        matches = [
            Match("__ w", "_W", "r1", offset=16, length=4, node_index=0)
        ]
        mask_ranges = [(6, 18)]
        
        is_valid, error = validate_no_masked_edits(matches, text, mask_ranges)
        
        assert not is_valid
