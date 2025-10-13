#!/usr/bin/env python3
"""
fixer/guards.py - Post-Checks and Safety Validators

Validates fixer model outputs to ensure they don't break Markdown structure.
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


# Forbidden tokens that indicate Markdown syntax
FORBIDDEN_TOKENS = [
    '```',      # Code fence
    '`',        # Inline code or fence
    '*',        # Emphasis or list
    '_',        # Emphasis
    '[',        # Link start
    ']',        # Link end
    '(',        # Link URL start
    ')',        # Link URL end
    '<',        # HTML or link
    '>',        # HTML or link
    'http://',  # URL
    'https://', # URL
    '##',       # Heading
    '---',      # Horizontal rule
    '~~~',      # Code fence
]


def check_forbidden_tokens(output: str) -> Tuple[bool, str]:
    """
    Check if output contains markdown tokens.
    
    Args:
        output: Fixer model output
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    for token in FORBIDDEN_TOKENS:
        if token in output:
            return False, f"Contains forbidden token: '{token}'"
    
    return True, ""


def check_length_delta(original: str, output: str, max_ratio: float) -> Tuple[bool, str]:
    """
    Check if output growth exceeds maximum ratio.
    
    Args:
        original: Original text
        output: Fixed text
        max_ratio: Maximum growth ratio (e.g., 0.20 for 20%)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    orig_len = len(original)
    out_len = len(output)
    
    if orig_len == 0:
        # Edge case: empty input
        if out_len > 0:
            return False, "Output non-empty for empty input"
        return True, ""
    
    growth_ratio = (out_len - orig_len) / orig_len
    
    if growth_ratio > max_ratio:
        return False, f"Growth {growth_ratio:.1%} exceeds limit {max_ratio:.1%}"
    
    # Also check for excessive shrinkage (> 50% reduction might indicate hallucination)
    if growth_ratio < -0.5:
        return False, f"Shrinkage {abs(growth_ratio):.1%} exceeds safe limit"
    
    return True, ""


def check_is_text(output: str) -> Tuple[bool, str]:
    """
    Check if output is valid text (not empty, not just whitespace).
    
    Args:
        output: Fixer model output
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not output:
        return False, "Empty output"
    
    if not output.strip():
        return False, "Output is only whitespace"
    
    return True, ""


def validate_output(
    original: str,
    output: str,
    config: Dict[str, Any]
) -> Tuple[bool, str, str]:
    """
    Run all validation checks on fixer output.
    
    Args:
        original: Original text span
        output: Fixed text from model
        config: Fixer configuration
    
    Returns:
        Tuple of (is_valid, cleaned_output, rejection_reason)
        - If valid: (True, cleaned_output, "")
        - If invalid: (False, original, rejection_reason)
    """
    # Strip whitespace from output
    cleaned = output.strip()
    
    # Check 1: Is it text?
    is_valid, error = check_is_text(cleaned)
    if not is_valid:
        logger.debug(f"Rejected: {error}")
        return False, original, "empty_or_non_text"
    
    # Check 2: Forbidden tokens
    forbid_tokens = config.get('forbid_markdown_tokens', True)
    if forbid_tokens:
        is_valid, error = check_forbidden_tokens(cleaned)
        if not is_valid:
            logger.debug(f"Rejected: {error}")
            return False, original, "forbidden_tokens"
    
    # Check 3: Length delta
    max_ratio = config.get('node_max_growth_ratio', 0.20)
    is_valid, error = check_length_delta(original, cleaned, max_ratio)
    if not is_valid:
        logger.debug(f"Rejected: {error}")
        return False, original, "growth_limit"
    
    # All checks passed
    return True, cleaned, ""


def check_file_growth(
    original_text: str,
    fixed_text: str,
    max_ratio: float
) -> Tuple[bool, float]:
    """
    Check if total file growth exceeds limit.
    
    Args:
        original_text: Original full text
        fixed_text: Fixed full text
        max_ratio: Maximum growth ratio (e.g., 0.05 for 5%)
    
    Returns:
        Tuple of (is_valid, actual_ratio)
    """
    orig_len = len(original_text)
    fixed_len = len(fixed_text)
    
    if orig_len == 0:
        return True, 0.0
    
    growth_ratio = (fixed_len - orig_len) / orig_len
    is_valid = abs(growth_ratio) <= max_ratio
    
    return is_valid, growth_ratio
