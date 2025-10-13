#!/usr/bin/env python3
"""
fixer/fixer.py - Main Fixer Orchestration

Applies light polish to text nodes with safety guardrails.
"""

import logging
import re
from typing import Dict, Any, List, Tuple

from .client import FixerClient
from .prompt import get_prompts
from .guards import validate_output, check_file_growth

logger = logging.getLogger(__name__)


def split_long_node(text: str, max_chars: int = 600) -> List[str]:
    """
    Split text node into sentence-like spans if needed.
    
    Args:
        text: Text to split
        max_chars: Maximum characters per span
    
    Returns:
        List of text spans
    """
    if len(text) <= max_chars:
        return [text]
    
    # Simple sentence splitter - split on sentence boundaries
    # Pattern: period/exclamation/question followed by space and capital letter
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(sentence_pattern, text)
    
    spans = []
    current_span = ""
    
    for sentence in sentences:
        if len(current_span) + len(sentence) <= max_chars:
            current_span += sentence
        else:
            if current_span:
                spans.append(current_span)
            current_span = sentence
    
    if current_span:
        spans.append(current_span)
    
    # Fallback: if any span is still too long, split on whitespace
    final_spans = []
    for span in spans:
        if len(span) <= max_chars:
            final_spans.append(span)
        else:
            # Split long span on whitespace
            words = span.split()
            temp_span = ""
            for word in words:
                if len(temp_span) + len(word) + 1 <= max_chars:
                    temp_span += (" " if temp_span else "") + word
                else:
                    if temp_span:
                        final_spans.append(temp_span)
                    temp_span = word
            if temp_span:
                final_spans.append(temp_span)
    
    return final_spans if final_spans else [text]


def fix_span(
    span: str,
    client: FixerClient,
    config: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Fix single text span with model call and validation.
    
    Args:
        span: Text span to fix
        client: Fixer model client
        config: Fixer configuration
    
    Returns:
        Tuple of (fixed_text, stats_dict)
    """
    stats = {
        "span_fixed": False,
        "rejection_reason": None
    }
    
    # Build prompts
    system_prompt, user_prompt = get_prompts(span, config)
    
    # Call model
    try:
        response, error = client.call_model(system_prompt, user_prompt)
        
        if error:
            logger.debug(f"Model call failed: {error}")
            stats["rejection_reason"] = "timeout" if "Timeout" in error else "non_response"
            return span, stats  # Fail-safe to original
        
        # Validate output
        is_valid, fixed_text, rejection_reason = validate_output(span, response, config)
        
        if not is_valid:
            logger.debug(f"Output validation failed: {rejection_reason}")
            stats["rejection_reason"] = rejection_reason
            return span, stats  # Fail-safe to original
        
        # Success!
        stats["span_fixed"] = True
        return fixed_text, stats
    
    except ConnectionError:
        # Re-raise for exit code 2
        raise
    except Exception as e:
        logger.warning(f"Unexpected error fixing span: {e}")
        stats["rejection_reason"] = "exception"
        return span, stats


def apply_fixer(
    text: str,
    text_nodes: List[Dict[str, Any]],
    mask_table: Dict[str, str],
    config: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Main entry point: fix all text nodes and return updated text.
    
    Args:
        text: Full markdown text (with masks)
        text_nodes: List of text node dicts from Phase 1 (with 'start', 'end', 'text')
        mask_table: Mask table from Phase 1
        config: Fixer configuration
    
    Returns:
        Tuple of (fixed_text, stats_dict)
    
    Raises:
        ConnectionError: If model server unreachable after retries
    """
    # Initialize stats
    stats = {
        "phase": "fixer",
        "model": config.get('model', 'qwen2.5-1.5b-instruct'),
        "nodes_seen": 0,
        "spans_total": 0,
        "spans_fixed": 0,
        "spans_rejected": 0,
        "rejections": {
            "forbidden_tokens": 0,
            "growth_limit": 0,
            "empty_or_non_text": 0,
            "timeout": 0,
            "non_response": 0,
            "exception": 0
        },
        "file_growth_ratio": 0.0,
        "deterministic": config.get('seed') is not None
    }
    
    # Create client
    client = FixerClient(config)
    
    # Track text modifications
    # Build new text by replacing text node spans
    result_text = text
    offset_delta = 0  # Track how offsets change as we modify text
    
    for node in text_nodes:
        stats["nodes_seen"] += 1
        
        node_text = node['text']
        node_start = node['start']
        node_end = node['end']
        
        # Skip very short nodes (< 20 chars)
        if len(node_text.strip()) < 20:
            logger.debug(f"Skipping short node: {len(node_text)} chars")
            continue
        
        # Split long nodes
        spans = split_long_node(node_text)
        stats["spans_total"] += len(spans)
        
        # Fix each span
        fixed_spans = []
        for span in spans:
            fixed_span, span_stats = fix_span(span, client, config)
            fixed_spans.append(fixed_span)
            
            if span_stats["span_fixed"]:
                stats["spans_fixed"] += 1
            else:
                stats["spans_rejected"] += 1
                rejection_reason = span_stats.get("rejection_reason")
                if rejection_reason and rejection_reason in stats["rejections"]:
                    stats["rejections"][rejection_reason] += 1
        
        # Reassemble node
        fixed_node_text = "".join(fixed_spans)
        
        # Replace in result text (accounting for offset delta)
        adjusted_start = node_start + offset_delta
        adjusted_end = node_end + offset_delta
        
        result_text = (
            result_text[:adjusted_start] +
            fixed_node_text +
            result_text[adjusted_end:]
        )
        
        # Update offset delta
        length_change = len(fixed_node_text) - len(node_text)
        offset_delta += length_change
    
    # Check file-level growth
    file_max_ratio = config.get('file_max_growth_ratio', 0.05)
    is_valid, growth_ratio = check_file_growth(text, result_text, file_max_ratio)
    stats["file_growth_ratio"] = growth_ratio
    
    if not is_valid:
        logger.warning(f"File growth {growth_ratio:.1%} exceeds limit {file_max_ratio:.1%}")
        logger.warning("Reverting to original text")
        return text, stats
    
    logger.info(f"Fixer complete: {stats['spans_fixed']}/{stats['spans_total']} spans fixed")
    logger.info(f"File growth: {growth_ratio:.1%}")
    
    return result_text, stats
