#!/usr/bin/env python3
"""
Applier: Left-to-right non-overlapping edit engine

Applies matches to text nodes in a deterministic, idempotent manner.
"""

from typing import List, Tuple, Dict, Any
import logging

from .matcher import Match

logger = logging.getLogger(__name__)


def apply_matches_to_text(text: str, matches: List[Match]) -> Tuple[str, Dict[str, int]]:
    """
    Apply all matches to text in a single pass.
    
    Args:
        text: The text to edit
        matches: List of non-overlapping matches, sorted by offset
    
    Returns:
        Tuple of (edited_text, stats_dict)
    """
    if not matches:
        return text, {
            'replacements_applied': 0,
            'length_delta': 0
        }
    
    # Sort matches by offset (should already be sorted, but ensure)
    sorted_matches = sorted(matches, key=lambda m: m.offset)
    
    # Build result by processing matches left-to-right
    result_parts = []
    current_pos = 0
    replacements_applied = 0
    total_length_delta = 0
    
    for match in sorted_matches:
        # Add text before this match
        result_parts.append(text[current_pos:match.offset])
        
        # Add replacement
        result_parts.append(match.replace)
        
        # Update position
        current_pos = match.end_offset()
        
        # Update stats
        replacements_applied += 1
        total_length_delta += len(match.replace) - len(match.find)
    
    # Add remaining text after last match
    result_parts.append(text[current_pos:])
    
    result = ''.join(result_parts)
    
    stats = {
        'replacements_applied': replacements_applied,
        'length_delta': total_length_delta
    }
    
    return result, stats


def apply_matches_to_nodes(
    text_nodes: List[str],
    matches: List[Match]
) -> Tuple[List[str], Dict[str, int]]:
    """
    Apply matches to multiple text nodes.
    
    Args:
        text_nodes: List of text node contents
        matches: List of all matches across nodes
    
    Returns:
        Tuple of (edited_nodes, combined_stats)
    """
    # Group matches by node index
    matches_by_node: Dict[int, List[Match]] = {}
    for match in matches:
        if match.node_index not in matches_by_node:
            matches_by_node[match.node_index] = []
        matches_by_node[match.node_index].append(match)
    
    # Apply to each node
    edited_nodes = []
    nodes_changed = 0
    total_replacements = 0
    total_length_delta = 0
    
    for node_idx, node_text in enumerate(text_nodes):
        node_matches = matches_by_node.get(node_idx, [])
        
        if node_matches:
            edited_text, stats = apply_matches_to_text(node_text, node_matches)
            edited_nodes.append(edited_text)
            
            nodes_changed += 1
            total_replacements += stats['replacements_applied']
            total_length_delta += stats['length_delta']
            
            logger.debug(
                f"Node {node_idx}: {stats['replacements_applied']} replacements, "
                f"delta {stats['length_delta']:+d} chars"
            )
        else:
            # No changes to this node
            edited_nodes.append(node_text)
    
    combined_stats = {
        'nodes_changed': nodes_changed,
        'replacements_applied': total_replacements,
        'length_delta': total_length_delta
    }
    
    return edited_nodes, combined_stats


def apply_plan_to_text(
    text: str,
    plan_items: List[Dict[str, str]],
    config: Dict[str, Any] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Apply a complete plan to text (single-node version).
    
    Args:
        text: The text to edit
        plan_items: List of plan items with find/replace/reason
        config: Optional configuration
    
    Returns:
        Tuple of (edited_text, report_dict)
    """
    from .matcher import find_matches_in_nodes, remove_overlapping_matches
    
    config = config or {}
    
    # Treat as single text node
    text_nodes = [text]
    
    # Find all matches
    all_matches = find_matches_in_nodes(text_nodes, plan_items)
    
    # Remove overlaps
    non_overlapping, overlaps_removed = remove_overlapping_matches(all_matches)
    
    logger.info(
        f"Found {len(all_matches)} total matches, "
        f"removed {overlaps_removed} overlapping"
    )
    
    # Apply matches
    edited_nodes, stats = apply_matches_to_nodes(text_nodes, non_overlapping)
    
    # Build report
    report = {
        'phase': 'apply',
        'files': 1,
        'nodes_changed': stats['nodes_changed'],
        'replacements_applied': stats['replacements_applied'],
        'replacements_skipped_overlap': overlaps_removed,
        'replacements_skipped_no_match': len(plan_items) - len(all_matches),
        'length_delta': stats['length_delta'],
        'growth_ratio': stats['length_delta'] / max(len(text), 1) if text else 0.0
    }
    
    return edited_nodes[0], report


def check_idempotence(
    original_text: str,
    plan_items: List[Dict[str, str]],
    config: Dict[str, Any] = None
) -> bool:
    """
    Verify that applying the plan twice yields the same result.
    
    Args:
        original_text: The original text
        plan_items: The plan to apply
        config: Optional configuration
    
    Returns:
        True if idempotent, False otherwise
    """
    # Apply once
    first_pass, _ = apply_plan_to_text(original_text, plan_items, config)
    
    # Apply again to the result
    second_pass, report = apply_plan_to_text(first_pass, plan_items, config)
    
    # Should be identical
    is_idempotent = (first_pass == second_pass)
    
    if not is_idempotent:
        logger.warning(
            f"Idempotence check failed! "
            f"Second pass made {report['replacements_applied']} changes"
        )
    
    return is_idempotent
