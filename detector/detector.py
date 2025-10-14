#!/usr/bin/env python3
"""
detector/detector.py - Main Orchestrator

Coordinates prompt construction, model calling, plan validation, and reporting.
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from .client import ModelClient
from .schema import validate_plan, merge_plans, ReplacementItem, plan_to_json
from .chunking import chunk_text_node, should_skip_node

logger = logging.getLogger(__name__)


# System prompt template
SYSTEM_PROMPT = """You propose STRICT JSON replacement plans to fix mechanical text artifacts that harm TTS,
without changing meaning or style. Output JSON only. No prose.

Allowed reasons:
- TTS_SPACED (inter-letter or comma/dot-separated letters)
- UNICODE_STYLIZED (compat forms to ASCII; keep accents if real word)
- CASE_GLITCH (random mid-word casing in normal prose)
- SIMPLE_PUNCT (stray repeated punctuation in pure prose)

Rules:
- Propose at most {max_items} items.
- Use literal "find" substrings from the provided TEXT ONLY.
- "replace" must be plain text; no markdown/links/masks; length increase ≤10 chars.
- If nothing clearly fixable: return [].

Output format:
[
  {{"find": "F ʟ ᴀ s ʜ", "replace": "Flash", "reason": "TTS_SPACED"}},
  {{"find": "Bʏ Mʏ Rᴇsᴏʟᴠᴇ", "replace": "By My Resolve", "reason": "UNICODE_STYLIZED"}}
]"""


def build_user_prompt(text_span: str, config: Dict[str, Any]) -> str:
    """
    Build user prompt for a text span.
    
    Args:
        text_span: The text to analyze
        config: Configuration dict
    
    Returns:
        User prompt string
    """
    locale = config.get('locale', 'en')
    max_items = config.get('json_max_items', 16)
    
    prompt = f"""LANG={locale}
MAX_ITEMS={max_items}
TEXT:
<<<
{text_span}
>>>
Return JSON array only."""
    
    return prompt


def process_text_node(node_text: str, config: Dict[str, Any], client: ModelClient) -> Tuple[List[ReplacementItem], Dict[str, int]]:
    """
    Process a single text node through detector.
    
    Args:
        node_text: Text content of the node
        config: Configuration dict
        client: ModelClient instance
    
    Returns:
        Tuple of (valid_items, stats_dict)
    """
    stats = {
        'nodes_seen': 1,
        'nodes_skipped': 0,
        'spans_checked': 0,
        'model_calls': 0,
        'model_errors': 0,
        'json_parse_errors': 0,
        'suggestions_valid': 0,
        'suggestions_rejected': 0,
    }
    
    rejections = defaultdict(int)
    
    # Pre-flight check
    should_skip, skip_reason = should_skip_node(node_text, config)
    if should_skip:
        stats['nodes_skipped'] = 1
        logger.debug(f"Skipping node: {skip_reason}")
        return [], stats
    
    # Chunk the node
    chunks = chunk_text_node(node_text, config)
    stats['spans_checked'] = len(chunks)
    
    # Process each chunk
    all_plans = []
    
    for chunk_text, start_offset, end_offset in chunks:
        logger.debug("Detector chunk preview: %s", chunk_text[:256])
        # Build prompts
        system_prompt = SYSTEM_PROMPT.format(
            max_items=config.get('json_max_items', 16)
        )
        user_prompt = build_user_prompt(chunk_text, config)
        
        # Call model
        stats['model_calls'] += 1
        response, error = client.call_model(system_prompt, user_prompt)
        
        if error:
            stats['model_errors'] += 1
            logger.warning(f"Model call failed: {error}")
            continue
        
        # Extract JSON
        json_plan, json_error = client.extract_json(response)
        if json_error:
            stats['json_parse_errors'] += 1
            logger.warning(f"JSON extraction failed: {json_error}")
            continue
        if isinstance(json_plan, list) and not json_plan:
            logger.info("Detector model returned empty plan. Raw response: %s", response)
        
        # Validate plan
        valid_items, chunk_rejections = validate_plan(json_plan, chunk_text, config)
        
        # Update stats
        stats['suggestions_valid'] += len(valid_items)
        stats['suggestions_rejected'] += sum(chunk_rejections.values())
        
        for reason, count in chunk_rejections.items():
            rejections[reason] += count
        
        all_plans.append(valid_items)
    
    # Merge plans from overlapping chunks (de-duplicate)
    merged_plan = merge_plans(all_plans)
    
    # Add rejection breakdown to stats
    stats['rejections'] = dict(rejections)
    
    return merged_plan, stats


def run_detector(text_nodes: List[str], config: Dict[str, Any]) -> Tuple[List[ReplacementItem], Dict[str, Any]]:
    """
    Run detector on multiple text nodes.
    
    Args:
        text_nodes: List of text node contents
        config: Configuration dict
    
    Returns:
        Tuple of (merged_plan, report_dict)
    """
    if not config.get('enabled', True):
        logger.info("Detector disabled in config")
        return [], {
            'phase': 'detector',
            'disabled': True,
            'reason': 'detector.disabled'
        }
    
    # Initialize client
    client = ModelClient(config)
    
    # Aggregate stats
    total_stats = {
        'phase': 'detector',
        'model': config.get('model', 'unknown'),
        'nodes_seen': 0,
        'nodes_skipped': 0,
        'spans_checked': 0,
        'model_calls': 0,
        'model_errors': 0,
        'json_parse_errors': 0,
        'suggestions_valid': 0,
        'suggestions_rejected': 0,
        'rejections': defaultdict(int),
        'by_reason': defaultdict(int),
    }
    
    all_plans = []
    
    # Process each node
    for node_text in text_nodes:
        plan, stats = process_text_node(node_text, config, client)
        all_plans.append(plan)
        
        # Aggregate stats
        for key in ['nodes_seen', 'nodes_skipped', 'spans_checked', 'model_calls', 
                    'model_errors', 'json_parse_errors', 'suggestions_valid', 'suggestions_rejected']:
            total_stats[key] += stats.get(key, 0)
        
        # Aggregate rejections
        for reason, count in stats.get('rejections', {}).items():
            total_stats['rejections'][reason] += count
        
        # Count by reason
        for item in plan:
            total_stats['by_reason'][item.reason] += 1
    
    # Merge all plans (de-duplicate across nodes)
    final_plan = merge_plans(all_plans)
    
    # Convert defaultdicts to regular dicts for JSON serialization
    total_stats['rejections'] = dict(total_stats['rejections'])
    total_stats['by_reason'] = dict(total_stats['by_reason'])
    
    logger.info(f"Detector complete: {len(final_plan)} replacements proposed")
    logger.info(f"Stats: {total_stats}")
    
    return final_plan, total_stats


def apply_plan_to_text(text: str, plan: List[ReplacementItem]) -> Tuple[str, int]:
    """
    Apply a plan to text (for testing - Phase 7 will do the real application).
    
    This is a simple literal replacement for validation purposes.
    Phase 7 will do proper anchored matching with structural validation.
    
    Args:
        text: Original text
        plan: List of replacements
    
    Returns:
        Tuple of (modified_text, replacements_applied)
    """
    result = text
    applied = 0
    
    # Apply replacements (sorted by offset if we had them, but for now just iterate)
    for item in plan:
        if item.find in result:
            result = result.replace(item.find, item.replace, 1)  # Replace first occurrence only
            applied += 1
    
    return result, applied
