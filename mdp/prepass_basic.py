#!/usr/bin/env python3
"""
Deterministic text normalization for Markdown text nodes.
"""

import re
import unicodedata
from typing import Dict, Any, Tuple
from collections import defaultdict

# Unicode characters to be stripped
ZERO_WIDTH_CHARS = [
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\ufeff',  # Byte order mark
]

# Bidirectional control characters
BIDI_CONTROLS = [
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e', '\u2066',
    '\u2067', '\u2068', '\u2069',
]

# Soft hyphen
SOFT_HYPHEN = '\u00ad'

def normalize_text_nodes(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    """
    Applies a series of deterministic normalization functions to a string
    and returns the normalized text along with a report of changes.
    """
    report = defaultdict(int)

    # 1. Unicode normalization (removed to allow for more granular control)

    # 2. Strip unwanted characters
    for char in ZERO_WIDTH_CHARS + BIDI_CONTROLS + [SOFT_HYPHEN]:
        count = text.count(char)
        if count > 0:
            text = text.replace(char, '')
            report['control_chars_stripped'] += count

    # 3. Handle non-breaking spaces
    if config.get('nbsp_handling', 'space') == 'space':
        count = text.count('\u00a0')
        if count > 0:
            text = text.replace('\u00a0', ' ')
            report['nbsp_converted_to_space'] += count

    # 4. Standardize punctuation
    text, punctuation_report = _standardize_punctuation(text, config)
    for k, v in punctuation_report.items():
        report[k] += v

    # 5. Repair spaced letters
    text, spaced_letters_report = _join_spaced_letters(text)
    for k, v in spaced_letters_report.items():
        report[k] += v

    # 6. Heal hyphenation
    text, hyphenation_report = _heal_hyphenation(text)
    for k, v in hyphenation_report.items():
        report[k] += v

    return text, dict(report)

def _standardize_punctuation(text: str, config: Dict[str, Any]) -> Tuple[str, Dict[str, int]]:
    report = defaultdict(int)
    if not config.get('normalize_punctuation', False):
        return text, dict(report)

    # Ellipsis
    count = text.count('…')
    if count > 0:
        text = text.replace('…', '...')
        report['ellipses_standardized'] += count

    # Quotes
    if config.get('quotes_policy') == 'straight':
        for find, replace in [('“', '"'), ('”', '"'), ('‘', "'"), ('’', "'")]:
            count = text.count(find)
            if count > 0:
                text = text.replace(find, replace)
                report['curly_quotes_straightened'] += count

    # Dashes
    dash_policy = config.get('dashes_policy', 'em')
    replacements = {
        'em': ('—', ['–', '--']),
        'en': ('–', ['—', '--']),
        'hyphen': ('-', ['—', '–', '--']),
    }

    replacer, to_replace = replacements[dash_policy]

    for dash in to_replace:
        count = text.count(dash)
        if count > 0:
            text = text.replace(dash, replacer)
            report['dashes_normalized'] += count

    return text, dict(report)

def _join_spaced_letters(text: str) -> Tuple[str, Dict[str, int]]:
    report = defaultdict(int)
    pattern = re.compile(r'\b([a-zA-Z](?:[\s.,]+[a-zA-Z])+)\b')

    new_text = []
    last_end = 0
    for match in pattern.finditer(text):
        if match.start() < last_end:
            continue

        new_text.append(text[last_end:match.start()])

        s = match.group(0)
        letters = re.findall(r'[a-zA-Z]', s)

        if len(letters) < 3:
            new_text.append(s)
            last_end = match.end()
            continue

        separators = re.findall(r'[\s.,]+', s)
        if all(sep == ' ' for sep in separators):
            if len(letters) < 4:
                new_text.append(s)
                last_end = match.end()
                continue

        replacement = "".join(letters)
        report['spaced_words_joined'] += 1
        new_text.append(replacement)
        last_end = match.end()

    new_text.append(text[last_end:])
    return "".join(new_text), dict(report)

def _heal_hyphenation(text: str) -> Tuple[str, Dict[str, int]]:
    report = defaultdict(int)
    # Looks for a hyphen at the end of a line followed by an alphabetic character.
    # Ensures we only join parts of words.
    pattern = re.compile(r'([a-zA-Z])-\n\s*([a-zA-Z])')

    def repl(match):
        report['hyphenation_healed'] += 1
        return match.group(1) + match.group(2)

    text = pattern.sub(repl, text)
    return text, dict(report)

def main():
    """CLI interface for prepass-basic normalization."""
    import argparse
    from pathlib import Path
    from . import config, markdown_adapter
    
    parser = argparse.ArgumentParser(
        description='Apply deterministic text normalization to Markdown files'
    )
    parser.add_argument('input_file', type=Path, help='Input Markdown file')
    parser.add_argument('-o', '--output', type=Path, help='Output file path')
    parser.add_argument('-c', '--config', type=Path, help='Configuration YAML file')
    parser.add_argument('--report', action='store_true', help='Print normalization report')
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = config.load_config(args.config) if args.config else config.load_config()
    
    # Read input file
    input_path = args.input_file
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    md_content = input_path.read_text(encoding='utf-8')
    
    # Process text spans
    text_spans = markdown_adapter.extract_text_spans(md_content)
    new_content_parts = []
    last_end = 0
    total_report = defaultdict(int)
    
    for span in text_spans:
        new_content_parts.append(md_content[last_end:span['start']])
        normalized_text, report = normalize_text_nodes(span['text'], cfg)
        new_content_parts.append(normalized_text)
        for k, v in report.items():
            total_report[k] += v
        last_end = span['end']
    
    new_content_parts.append(md_content[last_end:])
    normalized_content = "".join(new_content_parts)
    
    # Determine output path
    output_path = args.output
    if not output_path:
        # Default: create .tmp directory and output file
        tmp_dir = input_path.parent / '.tmp'
        tmp_dir.mkdir(exist_ok=True)
        output_path = tmp_dir / 'prepass_out.md'
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(normalized_content, encoding='utf-8')
    
    # Print summary
    print(f"Processing: {input_path}")
    if total_report:
        print("\nTransformations applied:")
        for key, count in sorted(total_report.items()):
            print(f"  - {key}: {count}")
    else:
        print("\nNo transformations needed.")
    print(f"\nOutput saved: {output_path}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())