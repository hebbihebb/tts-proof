#!/usr/bin/env python3
"""
Phase 4 - Advanced Pre-Pass: Casing, Punctuation, Numbers/Units

Policy-driven deterministic text cleanup that operates on text nodes only.
Runs after Phase 2 (Unicode & spacing) and before LLM steps.

Does NOT alter Markdown structure or masked regions.
"""

import re
from typing import Dict, Any, Tuple
from collections import defaultdict


def normalize_casing(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Normalize excessive all-caps words based on policy.
    
    Args:
        text: Input text string
        config: Casing configuration dict
    
    Returns:
        Tuple of (normalized_text, change_count)
    """
    if not config.get('normalize_shouting', True):
        return text, 0
    
    min_len = config.get('shouting_min_len', 4)
    acronyms = set(config.get('acronym_whitelist', []))
    protected = set(config.get('protected_lexicon', []))
    
    changes = 0
    words = []
    
    # Split on whitespace while preserving it
    parts = re.split(r'(\s+)', text)
    
    for part in parts:
        if not part or part.isspace():
            words.append(part)
            continue
        
        # Check if it's an all-caps word
        # Strip punctuation for checking but preserve it
        word_stripped = re.sub(r'^[^\w]+|[^\w]+$', '', part)
        
        if (len(word_stripped) >= min_len and 
            word_stripped.isupper() and 
            word_stripped.isalpha() and
            word_stripped not in acronyms and 
            word_stripped not in protected):
            
            # Normalize to title case (first letter upper, rest lower)
            # Preserve leading/trailing punctuation
            match = re.match(r'^([^\w]*)(\w+)([^\w]*)$', part)
            if match:
                prefix, word, suffix = match.groups()
                words.append(prefix + word.capitalize() + suffix)
                changes += 1
            else:
                words.append(part)
        else:
            words.append(part)
    
    return ''.join(words), changes


def collapse_punctuation_runs(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Collapse excessive punctuation runs based on policy.
    
    Examples:
        !!!!! → !
        ??!! → ?! (first-of-each policy)
    
    Args:
        text: Input text
        config: Punctuation configuration dict
    
    Returns:
        Tuple of (processed_text, change_count)
    """
    if not config.get('collapse_runs', True):
        return text, 0
    
    policy = config.get('runs_policy', 'first-of-each')
    changes = 0
    
    if policy == 'first-only':
        # Keep only the first punctuation mark in any run
        def replace_run(match):
            nonlocal changes
            run = match.group(0)
            if len(run) > 1:
                changes += 1
                return run[0]
            return run
        
        text = re.sub(r'[!?]+', replace_run, text)
    
    elif policy == 'first-of-each':
        # Keep first of each type: ??!! → ?!
        def replace_run(match):
            nonlocal changes
            run = match.group(0)
            seen = []
            for char in run:
                if char not in seen:
                    seen.append(char)
            result = ''.join(seen)
            if result != run:
                changes += 1
            return result
        
        text = re.sub(r'[!?]+', replace_run, text)
    
    return text, changes


def normalize_ellipsis(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Normalize ellipsis to configured format.
    
    Args:
        text: Input text
        config: Punctuation configuration dict
    
    Returns:
        Tuple of (processed_text, change_count)
    """
    ellipsis_style = config.get('ellipsis', 'three-dots')
    changes = 0
    
    if ellipsis_style == 'three-dots':
        # Convert unicode ellipsis to three dots
        if '…' in text:
            changes = text.count('…')
            text = text.replace('…', '...')
        
        # Normalize multiple dots to exactly three
        def replace_dots(match):
            nonlocal changes
            dots = match.group(0)
            if len(dots) != 3:
                changes += 1
                return '...'
            return dots
        
        text = re.sub(r'\.{2,}', replace_dots, text)
    
    elif ellipsis_style == 'unicode':
        # Convert three dots to unicode ellipsis
        def replace_dots(match):
            nonlocal changes
            changes += 1
            return '…'
        
        text = re.sub(r'\.{3,}', replace_dots, text)
    
    return text, changes


def normalize_quotes(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Normalize quote marks based on policy.
    
    Args:
        text: Input text
        config: Punctuation configuration dict
    
    Returns:
        Tuple of (processed_text, change_count)
    """
    changes = 0
    
    # Handle quotes
    quotes_policy = config.get('quotes', 'straight')
    if quotes_policy == 'straight':
        # Convert curly quotes to straight using explicit Unicode escapes
        curly_quotes = {
            '\u201c': '"',  # Left double quotation mark → straight double quote
            '\u201d': '"',  # Right double quotation mark → straight double quote
            '\u2018': "'",  # Left single quotation mark → straight apostrophe
            '\u2019': "'",  # Right single quotation mark → straight apostrophe
        }
        for curly, straight in curly_quotes.items():
            count = text.count(curly)
            if count > 0:
                changes += count
                text = text.replace(curly, straight)
    
    # Handle apostrophes separately
    apostrophe_policy = config.get('apostrophe', 'straight')
    if apostrophe_policy == 'straight':
        # Convert curly apostrophes to straight (already handled above for single quotes)
        pass
    
    return text, changes


def normalize_sentence_spacing(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Normalize spacing after sentence-ending punctuation.
    
    Args:
        text: Input text
        config: Punctuation configuration dict
    
    Returns:
        Tuple of (processed_text, change_count)
    """
    space_policy = config.get('space_after_sentence', 'single')
    changes = 0
    
    if space_policy == 'single':
        # Replace multiple spaces after sentence punctuation with single space
        def replace_spaces(match):
            nonlocal changes
            punct = match.group(1)
            spaces = match.group(2)
            if len(spaces) > 1:
                changes += 1
                return punct + ' '
            return match.group(0)
        
        text = re.sub(r'([.!?;:])(\s{2,})', replace_spaces, text)
    
    elif space_policy == 'double':
        # Ensure double space after period (only period, not other punctuation)
        def replace_spaces(match):
            nonlocal changes
            period = match.group(1)
            spaces = match.group(2)
            if len(spaces) != 2:
                changes += 1
                return period + '  '
            return match.group(0)
        
        text = re.sub(r'(\.)(\s+)(?=[A-Z])', replace_spaces, text)
    
    # Remove space before sentence-final punctuation (only if there's a space)
    def remove_space_before(match):
        nonlocal changes
        spaces = match.group(1)
        punct = match.group(2)
        # Only count changes if we're actually removing spaces
        if len(spaces) > 0:
            changes += 1
            return punct
        return match.group(0)
    
    text = re.sub(r'(\s+)([.!?;:,])', remove_space_before, text)
    
    return text, changes


def normalize_numbers_units(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Normalize spacing between numbers and units/symbols.
    
    Args:
        text: Input text
        config: Numbers/units configuration dict
    
    Returns:
        Tuple of (processed_text, changes_dict)
    """
    changes = defaultdict(int)
    
    # Percent sign handling
    if config.get('join_percent', True):
        # Remove space before %
        def fix_percent(match):
            changes['percent_joined'] += 1
            return match.group(1) + '%'
        
        text = re.sub(r'(\d)\s+%', fix_percent, text)
    
    # Unit spacing policy
    space_policy = config.get('space_before_unit', 'normal')
    
    # Common units: °C, °F, km, m, cm, mm, kg, g, mg, ms, s, etc.
    units_pattern = r'(\d)\s*(°[CF]|km|m|cm|mm|kg|g|mg|ms|s|mph|kph)\b'
    
    if space_policy == 'none':
        # Join number and unit
        def fix_unit(match):
            changes['unit_spaces'] += 1
            return match.group(1) + match.group(2)
        
        text = re.sub(units_pattern, fix_unit, text)
    
    elif space_policy == 'normal':
        # Ensure single normal space
        def fix_unit(match):
            num = match.group(1)
            unit = match.group(2)
            current = match.group(0)
            expected = num + ' ' + unit
            if current != expected:
                changes['unit_spaces'] += 1
                return expected
            return current
        
        text = re.sub(units_pattern, fix_unit, text)
    
    elif space_policy == 'nbsp':
        # Use non-breaking space (not implemented for simplicity)
        # Would replace with \u00A0
        pass
    
    return text, dict(changes)


def normalize_time_format(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Normalize time format (e.g., 5 pm → 5 p.m.).
    
    Args:
        text: Input text
        config: Numbers/units configuration dict
    
    Returns:
        Tuple of (processed_text, change_count)
    """
    time_style = config.get('time_style', 'p.m.')
    changes = 0
    
    # Match patterns like: 5pm, 5 pm, 5:30pm, 5:30 PM, etc.
    time_pattern = r'\b(\d{1,2}(?::\d{2})?)\s*(am|pm|AM|PM|a\.m\.|p\.m\.)\b'
    
    def replace_time(match):
        nonlocal changes
        time_num = match.group(1)
        meridiem = match.group(2).lower().replace('.', '')
        
        if time_style == 'p.m.':
            result = f"{time_num} {'a.m.' if meridiem.startswith('a') else 'p.m.'}"
        elif time_style == 'PM':
            result = f"{time_num} {'AM' if meridiem.startswith('a') else 'PM'}"
        elif time_style == 'pm':
            result = f"{time_num} {'am' if meridiem.startswith('a') else 'pm'}"
        else:
            return match.group(0)
        
        if result != match.group(0):
            changes += 1
        return result
    
    text = re.sub(time_pattern, replace_time, text)
    
    return text, changes


def remove_inline_footnotes(text: str, config: Dict[str, Any]) -> Tuple[str, int]:
    """
    Optionally remove inline footnote markers.
    
    Removes: [^1], [1], (1) style markers
    Does NOT touch footnote definitions.
    
    Args:
        text: Input text
        config: Footnotes configuration dict
    
    Returns:
        Tuple of (processed_text, change_count)
    """
    if not config.get('remove_inline_markers', False):
        return text, 0
    
    changes = 0
    
    # Remove inline markers: [^1], [1], (1)
    # But NOT footnote definitions like [^1]: text
    def replace_marker(match):
        nonlocal changes
        # Check if followed by colon (definition)
        full_match = match.group(0)
        if ':' not in full_match:
            changes += 1
            return ''
        return full_match
    
    # Match [^1], [1], (1) but not if followed by colon
    text = re.sub(r'\[\^\d+\](?!:)|\[\d+\](?!:)|\(\d+\)(?!:)', replace_marker, text)
    
    return text, changes


def apply_policies(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Apply all configured policies to text node content.
    
    This is the main entry point for Phase 4 processing.
    
    Args:
        text: Text node content to process
        config: Full prepass_advanced configuration dict
    
    Returns:
        Tuple of (processed_text, report_dict)
    """
    if not config.get('enabled', True):
        return text, {'prepass_advanced_disabled': 1}
    
    report = defaultdict(int)
    
    # Apply casing policies
    casing_config = config.get('casing', {})
    text, casing_changes = normalize_casing(text, casing_config)
    report['casing_normalized'] = casing_changes
    
    # Apply punctuation policies
    punct_config = config.get('punctuation', {})
    
    text, runs_changes = collapse_punctuation_runs(text, punct_config)
    report['runs_collapsed'] = runs_changes
    
    text, ellipsis_changes = normalize_ellipsis(text, punct_config)
    report['ellipsis'] = ellipsis_changes
    
    text, quotes_changes = normalize_quotes(text, punct_config)
    report['quotes'] = quotes_changes
    
    text, spacing_changes = normalize_sentence_spacing(text, punct_config)
    report['spacing'] = spacing_changes
    
    # Apply numbers/units policies
    numbers_config = config.get('numbers_units', {})
    
    text, numbers_changes = normalize_numbers_units(text, numbers_config)
    for key, value in numbers_changes.items():
        report[key] = value
    
    text, time_changes = normalize_time_format(text, numbers_config)
    report['times'] = time_changes
    
    # Apply footnote policies
    footnotes_config = config.get('footnotes', {})
    text, footnote_changes = remove_inline_footnotes(text, footnotes_config)
    report['footnotes_removed'] = footnote_changes
    
    return text, dict(report)


def main():
    """CLI interface for testing prepass_advanced."""
    import argparse
    import sys
    from pathlib import Path
    from . import config as cfg_module
    
    parser = argparse.ArgumentParser(
        description='Apply advanced pre-pass policies to text'
    )
    parser.add_argument('input_file', type=Path, help='Input text file')
    parser.add_argument('-o', '--output', type=Path, help='Output file path')
    parser.add_argument('-c', '--config', type=Path, help='Configuration YAML file')
    parser.add_argument('--report', action='store_true', help='Print processing report')
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = cfg_module.load_config(args.config) if args.config else cfg_module.load_config()
    advanced_config = cfg.get('prepass_advanced', {})
    
    # Read input
    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        return 1
    
    text = args.input_file.read_text(encoding='utf-8')
    
    # Process
    processed_text, report = apply_policies(text, advanced_config)
    
    # Output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(processed_text, encoding='utf-8')
        print(f"Processed: {args.input_file} → {args.output}")
    else:
        print(processed_text)
    
    if args.report and report:
        print("\nAdvanced Pre-Pass Report:")
        for key, count in sorted(report.items()):
            if count > 0:
                print(f"  {key}={count}", end='  ')
        print()
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
