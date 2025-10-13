#!/usr/bin/env python3
"""
Matcher: Literal, anchored matching for plan application

Finds all non-overlapping occurrences of literal find strings in text nodes.
Never touches masked regions or Markdown structure.
"""

from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class Match:
    """A single match of a plan item in text."""
    find: str
    replace: str
    reason: str
    offset: int  # Start position in text
    length: int  # Length of find string
    node_index: int  # Which text node this match is in
    
    def end_offset(self) -> int:
        """End position (exclusive) of this match."""
        return self.offset + self.length
    
    def overlaps(self, other: 'Match') -> bool:
        """Check if this match overlaps with another match."""
        return (self.offset < other.end_offset() and 
                other.offset < self.end_offset())


def find_all_matches(
    text: str, 
    find: str, 
    replace: str, 
    reason: str,
    node_index: int = 0
) -> List[Match]:
    """
    Find all non-overlapping occurrences of find string in text.
    
    Args:
        text: The text to search in
        find: The literal string to find
        replace: The replacement string
        reason: The reason for this replacement
        node_index: Index of the text node (for sorting)
    
    Returns:
        List of Match objects for all non-overlapping occurrences
    """
    if not find or not text:
        return []
    
    matches = []
    search_start = 0
    
    while True:
        # Find next occurrence
        pos = text.find(find, search_start)
        if pos == -1:
            break
        
        # Create match
        match = Match(
            find=find,
            replace=replace,
            reason=reason,
            offset=pos,
            length=len(find),
            node_index=node_index
        )
        
        matches.append(match)
        
        # Move search position past this match to avoid overlaps
        search_start = pos + len(find)
    
    return matches


def find_matches_in_nodes(
    text_nodes: List[str],
    plan_items: List[Dict[str, str]]
) -> List[Match]:
    """
    Find all matches across multiple text nodes for a plan.
    
    Args:
        text_nodes: List of text node contents
        plan_items: List of plan items with find/replace/reason
    
    Returns:
        List of all matches, sorted by node_index then offset
    """
    all_matches = []
    
    for node_idx, node_text in enumerate(text_nodes):
        for item in plan_items:
            find = item.get('find', '')
            replace = item.get('replace', '')
            reason = item.get('reason', '')
            
            if not find:
                continue
            
            # Find all occurrences in this node
            matches = find_all_matches(
                node_text, 
                find, 
                replace, 
                reason, 
                node_idx
            )
            all_matches.extend(matches)
    
    # Sort by node index, then offset, then longest find first (maximal munch)
    all_matches.sort(key=lambda m: (m.node_index, m.offset, -m.length))
    
    return all_matches


def remove_overlapping_matches(matches: List[Match]) -> Tuple[List[Match], int]:
    """
    Remove overlapping matches, keeping the first (longest) at each position.
    
    Args:
        matches: List of matches sorted by (node_index, offset, -length)
    
    Returns:
        Tuple of (non-overlapping matches, count of overlaps removed)
    """
    if not matches:
        return [], 0
    
    non_overlapping = []
    overlaps_removed = 0
    
    for match in matches:
        # Check if this match overlaps with any already accepted match
        # in the same node
        same_node_matches = [m for m in non_overlapping 
                            if m.node_index == match.node_index]
        
        has_overlap = any(match.overlaps(existing) 
                         for existing in same_node_matches)
        
        if not has_overlap:
            non_overlapping.append(match)
        else:
            overlaps_removed += 1
    
    return non_overlapping, overlaps_removed


def validate_no_masked_edits(
    matches: List[Match],
    text: str,
    mask_ranges: List[Tuple[int, int]] = None
) -> Tuple[bool, str]:
    """
    Validate that no match intersects with masked regions.
    
    Args:
        matches: List of matches to validate
        text: The full text being edited
        mask_ranges: List of (start, end) tuples for masked regions
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not mask_ranges:
        return True, ""
    
    for match in matches:
        for mask_start, mask_end in mask_ranges:
            # Check if match overlaps with this mask
            if (match.offset < mask_end and 
                mask_start < match.end_offset()):
                return False, (
                    f"Match at offset {match.offset} ('{match.find}') "
                    f"intersects masked region [{mask_start}, {mask_end})"
                )
    
    return True, ""
