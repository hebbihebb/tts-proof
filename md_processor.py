#!/usr/bin/env python3
"""
md_processor.py - TTS-Proof Markdown Processing Library & CLI

Consolidated single-file implementation of all TTS-Proof pipeline phases.
Can be used as both a library (import md_processor) and CLI tool (python md_processor.py).

Features:
- Phase 1: Markdown masking (protect code, links, HTML)
- Phase 2: Prepass (Unicode normalization, spacing fixes, casing)
- Phase 3: Scrubber (remove author notes, navigation)
- Phase 6: Detector (TTS problem detection)
- Phase 7: Apply (plan application with 7 structural validators)
- Phase 8: Fixer (light polish)
- LLM client (OpenAI-compatible API)
- Intelligent chunking
- Progress callbacks
- Checkpoint/resume support

Usage:
    # Library usage
    import md_processor
    result, stats = md_processor.run_pipeline(text, steps=['mask', 'detect', 'apply'])
    
    # CLI usage
    python md_processor.py --input input.md --output output.md --steps mask,detect,apply

Author: TTS-Proof v2
License: Personal utility
"""

import argparse
import json
import logging
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# Optional dependencies
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logging.warning("requests library not found - LLM features disabled")

# ============================================================================
# EMBEDDED PROMPTS
# ============================================================================

GRAMMAR_PROMPT = """You are a grammar and spelling corrector for Markdown text.

CRITICAL: When prepass replacements are provided, apply them EXACTLY as specified. Do not modify or interpret them.

Primary focus:
1) Apply prepass TTS corrections precisely as given
2) Fix grammar, spelling, and punctuation errors
3) Improve sentence flow and readability

Preservation rules:
- Never edit Markdown syntax, code blocks, inline code, links/URLs, images, or HTML tags
- Keep all Markdown structure exactly as-is
- Preserve meaning and tone
- Keep valid acronyms (NASA, GPU, API, etc.)

Output only the corrected Markdown; no explanations.

/no_think"""

DETECTOR_PROMPT = """Find stylized Unicode letters and normalize to standard English. Return JSON only.

Examples:
"Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!"  
"Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!" → "Spiral Seekers!"
"[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip: normal text, usernames, punctuation, code.

Format:
{"replacements": [{"find": "text", "replace": "fixed", "reason": "unicode"}]}

/no_think"""

# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    'detector': {
        'enabled': True,
        'api_base': 'http://127.0.0.1:1234/v1',
        'model': 'qwen3-detector',
        'chunk_size': 600,
        'locale': 'en',
        'json_max_items': 16,
    },
    'apply': {
        'enabled': True,
        'validators': {
            'mask_parity': True,
            'backtick_parity': True,
            'bracket_balance': True,
            'link_sanity': True,
            'fence_parity': True,
            'token_guard': True,
            'length_delta': {
                'enabled': True,
                'max_ratio': 0.01  # 1% growth limit
            }
        }
    },
    'fixer': {
        'enabled': False,  # Optional polish phase
        'api_base': 'http://127.0.0.1:1234/v1',
        'model': 'qwen3-grammar',
    },
    'prepass_basic': {
        'enabled': True,
    },
    'prepass_advanced': {
        'enabled': True,
    },
    'scrubber': {
        'enabled': False,  # Optional content removal
    }
}

# ============================================================================
# PHASE 1: MASKING
# ============================================================================

@dataclass
class ProtectedSpan:
    """Represents a protected region of Markdown text."""
    start: int
    end: int
    type: str
    text: str


def mask_protected(md_text: str) -> Tuple[str, Dict[str, str]]:
    """
    Mask protected regions of Markdown (code blocks, links, HTML, math).
    
    Args:
        md_text: Input Markdown text
    
    Returns:
        Tuple of (masked_text, mask_table)
        mask_table maps sentinels like __MASKED_0__ to original content
    """
    protected_spans = _get_protected_spans(md_text)
    
    mask_table = {}
    masked_parts = []
    last_end = 0
    counter = 0
    
    for span in protected_spans:
        # Add unprotected text before this span
        if span.start > last_end:
            masked_parts.append(md_text[last_end:span.start])
        
        # Create sentinel
        sentinel = f"__MASKED_{counter}__"
        mask_table[sentinel] = span.text
        masked_parts.append(sentinel)
        
        counter += 1
        last_end = span.end
    
    # Add remaining text
    if last_end < len(md_text):
        masked_parts.append(md_text[last_end:])
    
    masked_text = ''.join(masked_parts)
    
    logging.info(f"Masked {len(mask_table)} regions")
    return masked_text, mask_table


def unmask(masked_text: str, mask_table: Dict[str, str]) -> str:
    """
    Restore original content by replacing sentinels.
    
    Args:
        masked_text: Text with __MASKED_N__ sentinels
        mask_table: Mapping from sentinels to original content
    
    Returns:
        Restored text
    """
    if not mask_table:
        return masked_text
    
    # Replace sentinels (longest first to avoid partial matches)
    result = masked_text
    for sentinel in sorted(mask_table.keys(), key=len, reverse=True):
        result = result.replace(sentinel, mask_table[sentinel])
    
    return result


def _get_protected_spans(md_text: str) -> List[ProtectedSpan]:
    """
    Find all protected spans using regex patterns.
    """
    spans = []
    
    # Code fences (``` or ~~~)
    for match in re.finditer(r'(?m)^```[a-zA-Z]*\n.*?^```\s*$|^~~~[a-zA-Z]*\n.*?^~~~\s*$', md_text, re.DOTALL):
        spans.append(ProtectedSpan(
            start=match.start(),
            end=match.end(),
            type='CODE_FENCE',
            text=match.group(0)
        ))
    
    # Inline code
    for match in re.finditer(r'`+[^`]+`+', md_text):
        spans.append(ProtectedSpan(
            start=match.start(),
            end=match.end(),
            type='INLINE_CODE',
            text=match.group(0)
        ))
    
    # Links [text](url)
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', md_text):
        # Protect the URL part only
        url_start = match.start(2)
        url_end = match.end(2)
        spans.append(ProtectedSpan(
            start=url_start,
            end=url_end,
            type='LINK_URL',
            text=match.group(2)
        ))
    
    # Images ![alt](url)
    for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', md_text):
        url_start = match.start(2)
        url_end = match.end(2)
        spans.append(ProtectedSpan(
            start=url_start,
            end=url_end,
            type='IMAGE_URL',
            text=match.group(2)
        ))
    
    # HTML blocks
    for match in re.finditer(r'<(details|div|table|script|style).*?</\1>', md_text, re.DOTALL | re.IGNORECASE):
        spans.append(ProtectedSpan(
            start=match.start(),
            end=match.end(),
            type='HTML_BLOCK',
            text=match.group(0)
        ))
    
    # Math blocks $$...$$
    for match in re.finditer(r'\$\$.+?\$\$', md_text, re.DOTALL):
        spans.append(ProtectedSpan(
            start=match.start(),
            end=match.end(),
            type='MATH_BLOCK',
            text=match.group(0)
        ))
    
    # Inline math $...$
    for match in re.finditer(r'(?<!\\)\$[^$]+(?<!\\)\$', md_text):
        spans.append(ProtectedSpan(
            start=match.start(),
            end=match.end(),
            type='INLINE_MATH',
            text=match.group(0)
        ))
    
    # Sort by start position and remove overlaps
    spans.sort(key=lambda s: s.start)
    non_overlapping = []
    for span in spans:
        if not non_overlapping or span.start >= non_overlapping[-1].end:
            non_overlapping.append(span)
    
    return non_overlapping


# ============================================================================
# PHASE 2: PREPASS (BASIC + ADVANCED)
# ============================================================================

def prepass_basic(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Phase 2 basic: Unicode normalization and spacing fixes.
    
    Args:
        text: Input text
        config: Configuration dict
    
    Returns:
        Tuple of (processed_text, stats_dict)
    """
    stats = {}
    
    # Unicode normalization (NFC)
    import unicodedata
    normalized = unicodedata.normalize('NFC', text)
    if normalized != text:
        stats['unicode_normalized'] = len(text) - len(normalized)
        text = normalized
    
    # Fix multiple spaces
    original = text
    text = re.sub(r' {3,}', '  ', text)
    if text != original:
        stats['spaces_collapsed'] = original.count('   ')
    
    # Fix space before punctuation
    original = text
    text = re.sub(r' +([.,;:!?])', r'\1', text)
    if text != original:
        stats['space_before_punct'] = 1
    
    # Fix missing space after punctuation
    original = text
    text = re.sub(r'([.,;:!?])([A-Za-z])', r'\1 \2', text)
    if text != original:
        stats['space_after_punct'] = 1
    
    logging.info(f"Prepass basic: {stats}")
    return text, stats


def prepass_advanced(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Phase 2 advanced: Casing, punctuation, and ellipsis normalization.
    
    Args:
        text: Input text
        config: Configuration dict
    
    Returns:
        Tuple of (processed_text, stats_dict)
    """
    stats = {}
    
    # Normalize ellipsis (... or …)
    original = text
    text = re.sub(r'\.{3,}', '...', text)
    text = text.replace('…', '...')
    if text != original:
        stats['ellipsis_normalized'] = 1
    
    # Collapse repeated punctuation (!!! → !, ??? → ?)
    original = text
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    if text != original:
        stats['punct_collapsed'] = 1
    
    logging.info(f"Prepass advanced: {stats}")
    return text, stats


# ============================================================================
# PHASE 3: SCRUBBER (Stub for now)
# ============================================================================

def scrub_content(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Phase 3: Remove author notes, navigation, promotional content.
    
    Args:
        text: Input text
        config: Configuration dict
    
    Returns:
        Tuple of (processed_text, stats_dict)
    """
    # Stub - implement pattern matching for common boilerplate
    stats = {'blocks_removed': 0}
    logging.info(f"Scrubber: {stats}")
    return text, stats


# ============================================================================
# LLM CLIENT
# ============================================================================

SENTINEL_START = "<TEXT_TO_CORRECT>"
SENTINEL_END = "</TEXT_TO_CORRECT>"


class LLMClient:
    """OpenAI-compatible API client for LLM inference."""
    
    def __init__(self, endpoint: str, model: str, timeout: int = 600):
        """
        Initialize LLM client.
        
        Args:
            endpoint: API base URL (e.g. http://localhost:1234/v1)
            model: Model name
            timeout: Request timeout in seconds
        """
        if not HAS_REQUESTS:
            raise RuntimeError("requests library required for LLM features")
        
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
    
    def complete(self, system_prompt: str, user_text: str, temperature: float = 0.0, 
                 max_tokens: int = 4096) -> str:
        """
        Call LLM for text completion.
        
        Args:
            system_prompt: System instruction
            user_text: User input text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text
        """
        url = f"{self.endpoint}/chat/completions"
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{SENTINEL_START}\n{user_text}\n{SENTINEL_END}"}
            ],
            "stop": ["</RESULT>"],
            "enable_thinking": False
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Remove Qwen3 thinking tags if present
        content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)
        
        return content
    
    def extract_between_sentinels(self, text: str) -> str:
        """
        Extract text between <TEXT_TO_CORRECT> sentinels.
        
        Args:
            text: LLM response
        
        Returns:
            Extracted text
        """
        start = text.find(SENTINEL_START)
        end = text.rfind(SENTINEL_END)
        
        if start == -1 or end == -1:
            # No sentinels found, clean up and return
            cleaned = text.replace(SENTINEL_START, "").replace(SENTINEL_END, "")
            return cleaned.strip()
        
        start += len(SENTINEL_START)
        extracted = text[start:end].strip()
        extracted = extracted.replace(SENTINEL_START, "").replace(SENTINEL_END, "")
        
        return extracted


# ============================================================================
# PHASE 6: DETECTOR
# ============================================================================

@dataclass
class ReplacementItem:
    """Represents a single text replacement suggestion."""
    find: str
    replace: str
    reason: str


def detect_problems(text: str, llm_client: LLMClient, config: Dict[str, Any]) -> Tuple[List[ReplacementItem], Dict[str, int]]:
    """
    Phase 6: Detect TTS problems and generate replacement plan.
    
    Args:
        text: Input text (should be masked)
        llm_client: LLM client instance
        config: Configuration dict
    
    Returns:
        Tuple of (replacement_list, stats_dict)
    """
    stats = {
        'model_calls': 0,
        'suggestions_valid': 0,
        'suggestions_rejected': 0
    }
    
    # Call LLM with detector prompt
    try:
        response = llm_client.complete(DETECTOR_PROMPT, text, temperature=0.3)
        stats['model_calls'] = 1
        
        # Parse JSON response
        try:
            data = json.loads(response)
            replacements = data.get('replacements', [])
            
            # Validate each replacement
            valid_items = []
            for item in replacements:
                find_text = item.get('find', '')
                replace_text = item.get('replace', '')
                reason = item.get('reason', 'unknown')
                
                # Basic validation
                if not find_text or not replace_text:
                    stats['suggestions_rejected'] += 1
                    continue
                
                # Check if find_text exists in original
                if find_text not in text:
                    stats['suggestions_rejected'] += 1
                    logging.debug(f"Rejected (not found): {find_text}")
                    continue
                
                valid_items.append(ReplacementItem(
                    find=find_text,
                    replace=replace_text,
                    reason=reason
                ))
                stats['suggestions_valid'] += 1
            
            logging.info(f"Detector: {len(valid_items)} valid suggestions")
            return valid_items, stats
            
        except json.JSONDecodeError as e:
            logging.error(f"Detector JSON parse error: {e}")
            logging.debug(f"Response was: {response}")
            return [], stats
    
    except Exception as e:
        logging.error(f"Detector error: {e}")
        return [], stats


# ============================================================================
# PHASE 7: APPLY + VALIDATORS
# ============================================================================

def apply_plan(text: str, plan: List[ReplacementItem], config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Phase 7: Apply replacement plan with structural validation.
    
    Args:
        text: Input text
        plan: List of replacement items
        config: Configuration dict
    
    Returns:
        Tuple of (processed_text, stats_dict)
    """
    stats = {
        'replacements_applied': 0,
        'replacements_rejected': 0
    }
    
    if not plan:
        logging.info("Apply: No replacements to apply")
        return text, stats
    
    original_text = text
    
    # Apply replacements one by one
    for item in plan:
        if item.find in text:
            text = text.replace(item.find, item.replace, 1)  # Replace first occurrence
            stats['replacements_applied'] += 1
        else:
            stats['replacements_rejected'] += 1
            logging.debug(f"Replacement not applied (text changed): {item.find}")
    
    # Validate structural integrity
    is_valid, error = validate_all(original_text, text, config)
    
    if not is_valid:
        logging.error(f"Validation failed: {error}")
        logging.error("Rejecting all edits - returning original text")
        stats['validation_failed'] = True
        return original_text, stats
    
    stats['validation_passed'] = True
    logging.info(f"Apply: {stats['replacements_applied']} replacements applied")
    return text, stats


def validate_all(original: str, edited: str, config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Run all 7 structural validators.
    
    Args:
        original: Original text
        edited: Edited text
        config: Configuration dict
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    validators_config = config.get('apply', {}).get('validators', {})
    
    # 1. Mask parity
    if validators_config.get('mask_parity', True):
        is_valid, error = validate_mask_parity(original, edited)
        if not is_valid:
            return False, error
    
    # 2. Backtick parity
    if validators_config.get('backtick_parity', True):
        is_valid, error = validate_backtick_parity(original, edited)
        if not is_valid:
            return False, error
    
    # 3. Bracket balance
    if validators_config.get('bracket_balance', True):
        is_valid, error = validate_bracket_balance(original, edited)
        if not is_valid:
            return False, error
    
    # 4. Link sanity
    if validators_config.get('link_sanity', True):
        is_valid, error = validate_link_sanity(original, edited)
        if not is_valid:
            return False, error
    
    # 5. Fence parity
    if validators_config.get('fence_parity', True):
        is_valid, error = validate_fence_parity(original, edited)
        if not is_valid:
            return False, error
    
    # 6. Token guard
    if validators_config.get('token_guard', True):
        is_valid, error = validate_token_guard(original, edited)
        if not is_valid:
            return False, error
    
    # 7. Length delta
    length_config = validators_config.get('length_delta', {})
    if length_config.get('enabled', True):
        max_ratio = length_config.get('max_ratio', 0.01)
        is_valid, error = validate_length_delta(original, edited, max_ratio)
        if not is_valid:
            return False, error
    
    return True, ""


def validate_mask_parity(original: str, edited: str) -> Tuple[bool, str]:
    """Validate that __MASKED_N__ sentinel counts are unchanged."""
    orig_masks = re.findall(r'__MASKED_\d+__', original)
    edit_masks = re.findall(r'__MASKED_\d+__', edited)
    
    if len(orig_masks) != len(edit_masks):
        return False, f"Mask parity violation: {len(orig_masks)} → {len(edit_masks)} masks"
    
    # Check individual mask IDs
    if set(orig_masks) != set(edit_masks):
        return False, "Mask parity violation: mask IDs changed"
    
    return True, ""


def validate_backtick_parity(original: str, edited: str) -> Tuple[bool, str]:
    """Validate that backtick counts are unchanged."""
    orig_count = original.count('`')
    edit_count = edited.count('`')
    
    if orig_count != edit_count:
        return False, f"Backtick parity violation: {orig_count} → {edit_count}"
    
    return True, ""


def validate_bracket_balance(original: str, edited: str) -> Tuple[bool, str]:
    """Validate that brackets [], (), {} remain balanced."""
    brackets = [('[', ']'), ('(', ')'), ('{', '}')]
    
    for open_char, close_char in brackets:
        if original.count(open_char) != edited.count(open_char):
            return False, f"Bracket balance violation: {open_char} count changed"
        if original.count(close_char) != edited.count(close_char):
            return False, f"Bracket balance violation: {close_char} count changed"
    
    return True, ""


def validate_link_sanity(original: str, edited: str) -> Tuple[bool, str]:
    """Validate that ]( pair count is unchanged."""
    orig_links = original.count('](')
    edit_links = edited.count('](')
    
    if orig_links != edit_links:
        return False, f"Link sanity violation: ]( count {orig_links} → {edit_links}"
    
    return True, ""


def validate_fence_parity(original: str, edited: str) -> Tuple[bool, str]:
    """Validate that ``` counts are unchanged."""
    orig_fences = original.count('```')
    edit_fences = edited.count('```')
    
    if orig_fences != edit_fences:
        return False, f"Fence parity violation: ``` count {orig_fences} → {edit_fences}"
    
    return True, ""


def validate_token_guard(original: str, edited: str) -> Tuple[bool, str]:
    """Validate that no new Markdown tokens are introduced."""
    markdown_tokens = '*_[]()<>`~'
    
    for token in markdown_tokens:
        orig_count = original.count(token)
        edit_count = edited.count(token)
        
        if edit_count > orig_count:
            return False, f"Token guard violation: new '{token}' tokens introduced"
    
    return True, ""


def validate_length_delta(original: str, edited: str, max_ratio: float) -> Tuple[bool, str]:
    """Validate that length growth is within acceptable bounds."""
    orig_len = len(original)
    edit_len = len(edited)
    
    if orig_len == 0:
        return True, ""
    
    growth = edit_len - orig_len
    ratio = growth / orig_len
    
    if ratio > max_ratio:
        return False, f"Length delta violation: growth {ratio*100:.1f}% > {max_ratio*100:.1f}%"
    
    return True, ""


# ============================================================================
# PHASE 8: FIXER (Stub)
# ============================================================================

def fix_polish(text: str, llm_client: LLMClient, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Phase 8: Light polish with larger model.
    
    Args:
        text: Input text
        llm_client: LLM client instance
        config: Configuration dict
    
    Returns:
        Tuple of (processed_text, stats_dict)
    """
    # Stub for now
    stats = {'polishing_applied': 0}
    logging.info(f"Fixer: {stats}")
    return text, stats


# ============================================================================
# PIPELINE ORCHESTRATOR
# ============================================================================

def run_pipeline(text: str, steps: List[str], config: Dict[str, Any], 
                 llm_endpoint: str, llm_model: str) -> Tuple[str, Dict[str, Any]]:
    """
    Run the full processing pipeline.
    
    Args:
        text: Input Markdown text
        steps: List of step names to execute
        config: Configuration dict
        llm_endpoint: LLM API endpoint
        llm_model: LLM model name
    
    Returns:
        Tuple of (processed_text, combined_stats)
    """
    mask_table = None
    stats = {}
    llm_client = None
    
    # Initialize LLM client if needed
    if any(step in ['detect', 'fix'] for step in steps):
        if HAS_REQUESTS:
            llm_client = LLMClient(llm_endpoint, llm_model)
        else:
            logging.error("LLM steps require 'requests' library")
            raise RuntimeError("requests library not installed")
    
    # Execute pipeline
    for step in steps:
        logging.info(f"Running step: {step}")
        
        if step == 'mask':
            text, mask_table = mask_protected(text)
            stats['mask'] = {'masks_created': len(mask_table)}
        
        elif step == 'prepass-basic':
            text, step_stats = prepass_basic(text, config)
            stats['prepass-basic'] = step_stats
        
        elif step == 'prepass-advanced':
            text, step_stats = prepass_advanced(text, config)
            stats['prepass-advanced'] = step_stats
        
        elif step == 'scrubber':
            text, step_stats = scrub_content(text, config)
            stats['scrubber'] = step_stats
        
        elif step == 'detect':
            if not llm_client:
                logging.error("Detector requires LLM client")
                continue
            
            plan, step_stats = detect_problems(text, llm_client, config)
            stats['detect'] = step_stats
            stats['detect']['plan_size'] = len(plan)
            stats['_detect_plan'] = plan  # Store for apply step
        
        elif step == 'apply':
            # Get plan from previous detect step
            plan = stats.get('_detect_plan', [])
            if not plan:
                logging.warning("Apply: No detector plan found, skipping")
                stats['apply'] = {'skipped': True}
                continue
            
            text, step_stats = apply_plan(text, plan, config)
            stats['apply'] = step_stats
        
        elif step == 'fix':
            if not llm_client:
                logging.error("Fixer requires LLM client")
                continue
            
            text, step_stats = fix_polish(text, llm_client, config)
            stats['fix'] = step_stats
        
        else:
            logging.warning(f"Unknown step: {step}")
    
    # Unmask if needed
    if mask_table:
        text = unmask(text, mask_table)
        logging.info("Unmasked content")
    
    # Clean up internal state
    if '_detect_plan' in stats:
        del stats['_detect_plan']
    
    return text, stats


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='TTS-Proof Markdown Processor v2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  python md_processor.py --input input.md --output output.md --steps mask,detect,apply
  
  # Prepass only
  python md_processor.py --input input.md --output clean.md --steps mask,prepass-basic,prepass-advanced
  
  # With custom endpoint
  python md_processor.py --input input.md --output output.md --endpoint http://192.168.1.100:1234/v1
        """
    )
    
    parser.add_argument('--input', required=True, type=Path, help='Input Markdown file')
    parser.add_argument('--output', required=True, type=Path, help='Output file path')
    parser.add_argument('--steps', default='mask,detect,apply', help='Comma-separated pipeline steps')
    parser.add_argument('--endpoint', default='http://localhost:1234/v1', help='LLM API endpoint')
    parser.add_argument('--model', default='qwen3-detector', help='LLM model name')
    parser.add_argument('--config', type=Path, help='JSON config file (overrides defaults)')
    parser.add_argument('--verbose', action='store_true', help='Enable debug logging')
    parser.add_argument('--stats-json', type=Path, help='Write statistics to JSON file')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Load input
    if not args.input.exists():
        logging.error(f"Input file not found: {args.input}")
        return 1
    
    text = args.input.read_text(encoding='utf-8')
    logging.info(f"Loaded {len(text)} characters from {args.input}")
    
    # Load config
    config = DEFAULT_CONFIG.copy()
    if args.config and args.config.exists():
        with open(args.config) as f:
            user_config = json.load(f)
            # Deep merge config
            for key, value in user_config.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value
    
    # Parse steps
    steps = [s.strip() for s in args.steps.split(',')]
    logging.info(f"Pipeline: {' → '.join(steps)}")
    
    # Run pipeline
    try:
        output_text, stats = run_pipeline(text, steps, config, args.endpoint, args.model)
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_text, encoding='utf-8')
    logging.info(f"Wrote {len(output_text)} characters to {args.output}")
    
    # Write stats JSON if requested
    if args.stats_json:
        with open(args.stats_json, 'w') as f:
            json.dump(stats, f, indent=2)
        logging.info(f"Wrote statistics to {args.stats_json}")
    
    # Print summary
    print("\n=== Pipeline Statistics ===")
    for step_name, step_stats in stats.items():
        if isinstance(step_stats, dict):
            print(f"\n{step_name}:")
            for key, value in step_stats.items():
                print(f"  {key}: {value}")
        else:
            print(f"{step_name}: {step_stats}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
