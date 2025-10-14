#!/usr/bin/env python3
"""
detector/schema.py - JSON Plan Schema Validation

Strict validation for detector JSON output. Each plan is an array of replacement items.
"""

import re
from typing import List, Dict, Any, Tuple, Optional, Iterable
from dataclasses import dataclass


# Allowed reason categories
ALLOWED_REASONS = {
    'TTS_SPACED',          # Inter-letter or comma/dot-separated letters
    'UNICODE_STYLIZED',    # Compat forms to ASCII; keep accents if real word
    'CASE_GLITCH',         # Random mid-word casing in normal prose
    'SIMPLE_PUNCT',        # Stray repeated punctuation in pure prose
}

# Blocked categories (if model returns these, reject the item)
BLOCKED_REASONS = {
    'STYLE',               # Style changes
    'REWRITE',            # Content rewrites
    'MEANING_CHANGE',     # Semantic changes
}

# Forbidden characters in 'replace' field (Markdown/meta chars)
FORBIDDEN_REPLACE_CHARS = set('`*_[]()~<>')


def _normalize_reason(reason: str, allowed: Iterable[str]) -> Optional[str]:
    """Map free-form reason strings to an allowed detector category."""
    if not isinstance(reason, str):
        return None

    trimmed = reason.strip()
    if not trimmed:
        return None

    canonical_allowed = {entry.upper().replace('-', '_'): entry for entry in allowed}
    normalized = re.sub(r'[^A-Z]', '_', trimmed.upper())

    # Direct match (ignoring punctuation/spacing)
    if normalized in canonical_allowed:
        return canonical_allowed[normalized]

    # Heuristic mapping based on keywords
    lowered = trimmed.lower()
    if any(token in lowered for token in ('unicode', 'diacritic', 'accent', 'stylized')):
        return 'UNICODE_STYLIZED' if 'UNICODE_STYLIZED' in allowed else None
    if any(token in lowered for token in ('spaced', 'letter spacing', 'letter-spacing')):
        return 'TTS_SPACED' if 'TTS_SPACED' in allowed else None
    if any(token in lowered for token in ('case', 'uppercase', 'lowercase', 'caps')):
        return 'CASE_GLITCH' if 'CASE_GLITCH' in allowed else None
    if any(token in lowered for token in ('punct', 'dash', 'hyphen', 'ellipsis', 'quote', 'divider')):
        return 'SIMPLE_PUNCT' if 'SIMPLE_PUNCT' in allowed else None

    return None


@dataclass
class ReplacementItem:
    """A single replacement in the plan."""
    find: str
    replace: str
    reason: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'find': self.find,
            'replace': self.replace,
            'reason': self.reason
        }


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_item(item: Dict[str, Any], config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single replacement item against schema rules.
    
    Args:
        item: Dictionary with 'find', 'replace', 'reason' keys
        config: Configuration dict with limits
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required keys
    if not isinstance(item, dict):
        return False, "Item is not a dictionary"
    
    required_keys = {'find', 'replace', 'reason'}
    if not all(key in item for key in required_keys):
        return False, f"Missing required keys. Need: {required_keys}"
    
    find = item['find']
    replace = item['replace']
    reason = item['reason']
    
    # Validate 'find'
    if not isinstance(find, str) or not find:
        return False, "'find' must be non-empty string"
    
    if len(find) > 80:
        return False, "'find' exceeds 80 chars"
    
    if '\n' in find or '\r' in find:
        return False, "'find' contains newlines"
    
    # Validate 'replace'
    if not isinstance(replace, str):
        return False, "'replace' must be string"
    
    if len(replace) > 80:
        return False, "'replace' exceeds 80 chars"
    
    # Check for forbidden Markdown characters in 'replace'
    forbidden_found = [c for c in FORBIDDEN_REPLACE_CHARS if c in replace]
    if forbidden_found:
        return False, f"'replace' contains forbidden chars: {forbidden_found}"
    
    # Check length delta (per item)
    length_delta = len(replace) - len(find)
    if length_delta > 10:
        return False, f"Length delta {length_delta} exceeds +10 chars"
    
    # Validate 'reason'
    if not isinstance(reason, str):
        return False, "'reason' must be string"
    
    # Check against allowed reasons
    allowed = config.get('allow_categories', list(ALLOWED_REASONS))
    canonical_reason = _normalize_reason(reason, allowed)
    if canonical_reason is None:
        return False, f"'reason' '{reason}' not in allowed categories: {allowed}"

    # Check against blocked reasons
    blocked = config.get('block_categories', list(BLOCKED_REASONS))
    if canonical_reason in blocked:
        return False, f"'reason' '{reason}' is blocked"
    
    # Validate reason length (using canonical form)
    reason = canonical_reason
    max_reason_chars = config.get('max_reason_chars', 64)
    if len(reason) > max_reason_chars:
        return False, f"'reason' exceeds {max_reason_chars} chars"

    # Persist canonical reason for downstream steps
    item['reason'] = canonical_reason
    
    return True, ""


def validate_plan(plan: List[Dict[str, Any]], text_span: str, config: Dict[str, Any]) -> Tuple[List[ReplacementItem], Dict[str, int]]:
    """
    Validate entire plan against schema and chunk text.
    
    Args:
        plan: List of replacement items
        text_span: The text span this plan applies to
        config: Configuration dict
    
    Returns:
        Tuple of (valid_items, rejection_stats)
    """
    if not isinstance(plan, list):
        return [], {'schema': 1}
    
    max_items = config.get('json_max_items', 16)
    max_output_chars = config.get('max_output_chars', 2000)
    
    valid_items: List[ReplacementItem] = []
    rejections = {
        'schema': 0,
        'forbidden_chars': 0,
        'length_delta': 0,
        'no_match': 0,
        'duplicate': 0,
        'budget': 0,
    }
    
    # Check total items limit
    if len(plan) > max_items:
        rejections['budget'] = len(plan) - max_items
        plan = plan[:max_items]
    
    # Check total plan size
    plan_str = str(plan)
    if len(plan_str) > max_output_chars:
        rejections['budget'] += 1
        return [], rejections
    
    seen_pairs = set()
    total_length_delta = 0
    
    for item in plan:
        # Validate item schema
        is_valid, error_msg = validate_item(item, config)
        if not is_valid:
            if 'forbidden' in error_msg.lower():
                rejections['forbidden_chars'] += 1
            elif 'length delta' in error_msg.lower():
                rejections['length_delta'] += 1
            else:
                rejections['schema'] += 1
            continue
        
        # Check if 'find' exists in text span (literal match)
        find_str = item['find']
        if find_str not in text_span:
            rejections['no_match'] += 1
            continue
        
        # Check for duplicates
        pair = (item['find'], item['replace'])
        if pair in seen_pairs:
            rejections['duplicate'] += 1
            continue
        seen_pairs.add(pair)
        
        # Track cumulative length delta for this span
        length_delta = len(item['replace']) - len(item['find'])
        total_length_delta += length_delta
        
        # Accept the item
        valid_items.append(ReplacementItem(
            find=item['find'],
            replace=item['replace'],
            reason=item['reason']
        ))
    
    # Check cumulative length delta (max +5% of span length)
    max_span_delta = int(len(text_span) * 0.05)
    if total_length_delta > max_span_delta:
        # Reject entire plan if delta too large
        rejections['length_delta'] += len(valid_items)
        return [], rejections
    
    return valid_items, rejections


def plan_to_json(items: List[ReplacementItem]) -> List[Dict[str, str]]:
    """Convert list of ReplacementItems to JSON-serializable format."""
    return [item.to_dict() for item in items]


def merge_plans(plans: List[List[ReplacementItem]]) -> List[ReplacementItem]:
    """
    Merge multiple plans, de-duplicating by (find, replace) pair.
    
    Args:
        plans: List of replacement item lists
    
    Returns:
        Merged and de-duplicated list
    """
    seen = set()
    merged = []
    
    for plan in plans:
        for item in plan:
            pair = (item.find, item.replace)
            if pair not in seen:
                seen.add(pair)
                merged.append(item)
    
    return merged

