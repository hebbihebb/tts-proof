#!/usr/bin/env python3
"""
Structural Validator: 7 hard stops to prevent Markdown corruption

1. Mask/sentinel parity: __MASKED_N__ counts unchanged
2. Backtick parity: Total ` count unchanged, inline pairs remain even
3. Bracket balance: [], (), {} remain balanced
4. Link sanity: ]( pair count unchanged
5. Fence parity: ``` count remains even
6. Markdown token guard: No new *, _, [, ], (, ), `, ~, <, >
7. Length delta budget: Total growth ≤ max_ratio (default 1%)
"""

import re
from typing import Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Markdown tokens that should not be introduced
MARKDOWN_TOKENS = set('*_[]()` ~<>')


def validate_mask_parity(original: str, edited: str) -> Tuple[bool, str]:
    """
    Validate that masked sentinel counts remain identical.
    
    Args:
        original: Original text
        edited: Edited text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Extract all __MASKED_N__ sentinels
    mask_pattern = r'__MASKED_\d+__'
    
    original_masks = re.findall(mask_pattern, original)
    edited_masks = re.findall(mask_pattern, edited)
    
    if len(original_masks) != len(edited_masks):
        return False, (
            f"Mask parity violation: {len(original_masks)} masks in original, "
            f"{len(edited_masks)} in edited"
        )
    
    # Check each mask individually
    original_mask_counts = {}
    for mask in original_masks:
        original_mask_counts[mask] = original_mask_counts.get(mask, 0) + 1
    
    edited_mask_counts = {}
    for mask in edited_masks:
        edited_mask_counts[mask] = edited_mask_counts.get(mask, 0) + 1
    
    if original_mask_counts != edited_mask_counts:
        return False, (
            f"Mask parity violation: individual mask counts changed. "
            f"Original: {original_mask_counts}, Edited: {edited_mask_counts}"
        )
    
    return True, ""


def validate_backtick_parity(original: str, edited: str) -> Tuple[bool, str]:
    """
    Validate that backtick counts remain valid.
    
    - Total ` count unchanged
    - In non-fence regions, backtick count remains even (inline code pairing)
    
    Args:
        original: Original text
        edited: Edited text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    original_count = original.count('`')
    edited_count = edited.count('`')
    
    if original_count != edited_count:
        return False, (
            f"Backtick parity violation: {original_count} in original, "
            f"{edited_count} in edited"
        )
    
    # Check that inline code pairs remain valid (simplified check)
    # More sophisticated: ensure per-line or per-segment parity
    if original_count % 2 != edited_count % 2:
        return False, "Backtick parity violation: odd/even mismatch"
    
    return True, ""


def validate_bracket_balance(original: str, edited: str) -> Tuple[bool, str]:
    """
    Validate that brackets remain balanced.
    
    Checks [], (), {} balance independently.
    
    Args:
        original: Original text
        edited: Edited text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    def check_balance(text: str, open_char: str, close_char: str) -> Tuple[bool, int]:
        """Check if brackets are balanced, return (balanced, depth_reached)."""
        depth = 0
        max_depth = 0
        for char in text:
            if char == open_char:
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == close_char:
                depth -= 1
                if depth < 0:
                    return False, max_depth
        return depth == 0, max_depth
    
    brackets = [('[', ']'), ('(', ')'), ('{', '}')]
    
    for open_char, close_char in brackets:
        orig_balanced, orig_depth = check_balance(original, open_char, close_char)
        edit_balanced, edit_depth = check_balance(edited, open_char, close_char)
        
        if not orig_balanced:
            logger.warning(f"Original text has unbalanced {open_char}{close_char}")
        
        if not edit_balanced:
            return False, (
                f"Bracket balance violation: {open_char}{close_char} became unbalanced "
                f"after edit"
            )
        
        # Check counts match
        if original.count(open_char) != edited.count(open_char):
            return False, (
                f"Bracket balance violation: {open_char} count changed from "
                f"{original.count(open_char)} to {edited.count(open_char)}"
            )
        
        if original.count(close_char) != edited.count(close_char):
            return False, (
                f"Bracket balance violation: {close_char} count changed from "
                f"{original.count(close_char)} to {edited.count(close_char)}"
            )
    
    return True, ""


def validate_link_sanity(original: str, edited: str) -> Tuple[bool, str]:
    """
    Validate that Markdown link syntax remains sane.
    
    Checks that ]( pair count is unchanged.
    
    Args:
        original: Original text
        edited: Edited text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    original_links = original.count('](')
    edited_links = edited.count('](')
    
    if original_links != edited_links:
        return False, (
            f"Link sanity violation: ]( count changed from {original_links} "
            f"to {edited_links}"
        )
    
    return True, ""


def validate_fence_parity(original: str, edited: str) -> Tuple[bool, str]:
    """
    Validate that code fence counts remain even.
    
    ``` must appear in pairs (opening + closing).
    
    Args:
        original: Original text
        edited: Edited text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    original_fences = original.count('```')
    edited_fences = edited.count('```')
    
    if original_fences != edited_fences:
        return False, (
            f"Fence parity violation: ``` count changed from {original_fences} "
            f"to {edited_fences}"
        )
    
    if edited_fences % 2 != 0:
        return False, (
            f"Fence parity violation: ``` count is odd ({edited_fences}), "
            "must be even"
        )
    
    return True, ""


def validate_no_new_markdown_tokens(original: str, edited: str) -> Tuple[bool, str]:
    """
    Validate that no new Markdown tokens were introduced.
    
    Forbids introducing new: * _ [ ] ( ) ` ~ < >
    
    Args:
        original: Original text
        edited: Edited text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    violations = []
    
    for token in MARKDOWN_TOKENS:
        original_count = original.count(token)
        edited_count = edited.count(token)
        
        if edited_count > original_count:
            violations.append(
                f"'{token}' increased from {original_count} to {edited_count}"
            )
    
    if violations:
        return False, (
            f"Markdown token guard violation: new tokens introduced: "
            f"{', '.join(violations)}"
        )
    
    return True, ""


def validate_length_delta_budget(
    original: str,
    edited: str,
    max_ratio: float = 0.01
) -> Tuple[bool, str]:
    """
    Validate that total file growth is within budget.
    
    Args:
        original: Original text
        edited: Edited text
        max_ratio: Maximum allowed growth ratio (default 1%)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    original_len = len(original)
    edited_len = len(edited)
    
    if original_len == 0:
        # Empty file - allow any change
        return True, ""
    
    delta = edited_len - original_len
    growth_ratio = delta / original_len
    
    if growth_ratio > max_ratio:
        return False, (
            f"Length delta budget exceeded: {growth_ratio:.2%} growth "
            f"(max {max_ratio:.2%}). Delta: {delta:+d} chars "
            f"({original_len} → {edited_len})"
        )
    
    return True, ""


def validate_all(
    original: str,
    edited: str,
    config: Dict[str, Any] = None
) -> Tuple[bool, List[str]]:
    """
    Run all structural validators.
    
    Args:
        original: Original text
        edited: Edited text
        config: Optional configuration with validator settings
    
    Returns:
        Tuple of (all_passed, list_of_failure_reasons)
    """
    config = config or {}
    apply_config = config.get('apply', {})
    
    validators = [
        ('Mask Parity', validate_mask_parity),
        ('Backtick Parity', validate_backtick_parity),
        ('Bracket Balance', validate_bracket_balance),
        ('Link Sanity', validate_link_sanity),
        ('Fence Parity', validate_fence_parity),
        ('Markdown Token Guard', validate_no_new_markdown_tokens),
    ]
    
    failures = []
    
    # Run standard validators
    for name, validator_fn in validators:
        is_valid, error_msg = validator_fn(original, edited)
        if not is_valid:
            logger.error(f"Validation failed: {name} - {error_msg}")
            failures.append(f"{name}: {error_msg}")
    
    # Run length delta validator with config
    max_ratio = apply_config.get('max_file_growth_ratio', 0.01)
    is_valid, error_msg = validate_length_delta_budget(original, edited, max_ratio)
    if not is_valid:
        logger.error(f"Validation failed: Length Delta Budget - {error_msg}")
        failures.append(f"Length Delta Budget: {error_msg}")
    
    all_passed = len(failures) == 0
    
    if all_passed:
        logger.info("All structural validations passed")
    else:
        logger.error(f"Validation failed with {len(failures)} error(s)")
    
    return all_passed, failures
