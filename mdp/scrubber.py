#!/usr/bin/env python3
"""
Phase 3 - Boilerplate / Notes Scrubber

Detects and removes (or moves to appendix) non-story blocks such as:
- Author/Translator/Editor notes
- Navigation text
- Promotional/Social links
- Link farms
- Watermarks

All operations are deterministic and reversible.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict


class BlockCandidate:
    """Represents a block candidate for scrubbing."""
    
    def __init__(self, block_id: int, category: str, reason: str, 
                 content: str, position: str, confidence: float):
        self.block_id = block_id
        self.category = category
        self.reason = reason
        self.content = content
        self.position = position  # 'edge-top', 'edge-bottom', 'middle'
        self.confidence = confidence
    
    def __repr__(self):
        return f"Block({self.block_id}, {self.category}, {self.position}, conf={self.confidence:.2f})"


def split_into_blocks(text: str) -> List[str]:
    """
    Split Markdown text into logical blocks (paragraphs, headings, lists, etc.).
    Uses double newlines as primary delimiter.
    """
    # Split on double newlines but preserve them for reconstruction
    blocks = re.split(r'\n\n+', text)
    return [block.strip() for block in blocks if block.strip()]


def calculate_link_density(block: str) -> float:
    """
    Calculate the percentage of text that consists of links.
    Returns value between 0.0 and 1.0.
    """
    # Extract all link text: [text](url)
    link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
    links = re.findall(link_pattern, block)
    
    if not links:
        return 0.0
    
    # Count total characters in link text
    link_chars = sum(len(link_text) for link_text in links)
    
    # Count total non-whitespace characters
    total_chars = len(re.sub(r'\s+', '', block))
    
    if total_chars == 0:
        return 0.0
    
    return link_chars / total_chars


def count_links(block: str) -> int:
    """Count number of Markdown links in block."""
    link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
    return len(re.findall(link_pattern, block))


def detect_block_category(block: str, block_id: int, position: str, 
                          config: Dict[str, Any]) -> Optional[BlockCandidate]:
    """
    Detect if a block matches any scrubber category.
    Returns BlockCandidate if match found, None otherwise.
    """
    categories = config.get('categories', {})
    keywords = config.get('keywords', {})
    whitelist = config.get('whitelist', {})
    min_chars = config.get('min_chars_to_strip', 12)
    
    # Skip blocks that are too short
    if len(block) < min_chars:
        return None
    
    # Check whitelist headings first
    whitelist_headings = whitelist.get('headings_keep', [])
    for heading in whitelist_headings:
        if heading.lower() in block.lower():
            return None  # Whitelisted, don't scrub
    
    block_lower = block.lower()
    
    # 1. Check for author/translator/editor notes
    if categories.get('authors_notes', True) or categories.get('translators_notes', True) or categories.get('editors_notes', True):
        note_patterns = [
            r"\bauthor'?s?\s+note\b",
            r"\ba/?n\b",
            r"\btranslator'?s?\s+note\b",
            r"\bt/?n\b",
            r"\beditor'?s?\s+note\b",
            r"\be/?n\b",
            r"\bnote\s+from\s+(the\s+)?(author|translator|editor)\b",
        ]
        
        for pattern in note_patterns:
            if re.search(pattern, block_lower):
                category = 'authors_note'
                if 'translator' in block_lower:
                    category = 'translators_note'
                elif 'editor' in block_lower:
                    category = 'editors_note'
                
                # Check if this specific category is enabled
                category_key = category + 's'  # authors_notes, translators_notes, editors_notes
                if categories.get(category_key, True):
                    return BlockCandidate(
                        block_id=block_id,
                        category=category,
                        reason=f"Matched pattern: {pattern}",
                        content=block,
                        position=position,
                        confidence=0.9
                    )
    
    # 2. Check for navigation
    if categories.get('navigation', True):
        nav_keywords = keywords.get('navigation', [
            'previous chapter', 'next chapter', 'table of contents', 
            'back to top', 'return to', 'go to chapter'
        ])
        
        for keyword in nav_keywords:
            if keyword in block_lower:
                return BlockCandidate(
                    block_id=block_id,
                    category='navigation',
                    reason=f"Matched keyword: '{keyword}'",
                    content=block,
                    position=position,
                    confidence=0.85
                )
    
    # 3. Check for promos/ads/social
    if categories.get('promos_ads_social', True):
        promo_keywords = keywords.get('promos', [
            'patreon', 'ko-fi', 'buy me a coffee', 'discord', 
            'reddit', 'substack', 'support me on', 'join the discord',
            'follow me on'
        ])
        
        for keyword in promo_keywords:
            if keyword in block_lower:
                return BlockCandidate(
                    block_id=block_id,
                    category='promo_ad_social',
                    reason=f"Matched promo keyword: '{keyword}'",
                    content=block,
                    position=position,
                    confidence=0.8
                )
    
    # 4. Check for watermarks
    watermark_keywords = keywords.get('watermarks', [
        'read on', 'original at', 'source on', 
        'this chapter was brought to you by', 'posted on'
    ])
    
    for keyword in watermark_keywords:
        if keyword in block_lower:
            return BlockCandidate(
                block_id=block_id,
                category='watermark',
                reason=f"Matched watermark: '{keyword}'",
                content=block,
                position=position,
                confidence=0.75
            )
    
    # 5. Check for link farms
    if categories.get('link_farms', True):
        link_density = calculate_link_density(block)
        link_count = count_links(block)
        threshold = config.get('link_density_threshold', 0.50)
        
        if link_density >= threshold and link_count >= 2:
            return BlockCandidate(
                block_id=block_id,
                category='link_farm',
                reason=f"Link density {link_density:.0%} (threshold {threshold:.0%}), {link_count} links",
                content=block,
                position=position,
                confidence=0.7
            )
    
    return None


def scrub_text(text: str, config: Dict[str, Any], dry_run: bool = False) -> Tuple[str, List[BlockCandidate], Dict[str, int]]:
    """
    Main scrubber function. Detects and optionally removes boilerplate blocks.
    
    Args:
        text: Input Markdown text
        config: Scrubber configuration
        dry_run: If True, only detect blocks without removing them
    
    Returns:
        Tuple of (processed_text, candidates_list, report_dict)
    """
    if not config.get('enabled', True):
        return text, [], {'scrubber_disabled': 1}
    
    blocks = split_into_blocks(text)
    total_blocks = len(blocks)
    edge_window = config.get('edge_block_window', 6)
    
    candidates = []
    report = defaultdict(int)
    blocks_to_keep = []
    blocks_to_remove = []
    
    for i, block in enumerate(blocks):
        # Determine position with edge bias
        if i < edge_window:
            position = 'edge-top'
        elif i >= total_blocks - edge_window:
            position = 'edge-bottom'
        else:
            position = 'middle'
        
        candidate = detect_block_category(block, i, position, config)
        
        if candidate:
            # Apply edge bias: only scrub edge blocks unless very high confidence
            if position == 'middle' and candidate.confidence < 0.95:
                blocks_to_keep.append(block)
                report['kept_middle_bias'] += 1
            else:
                candidates.append(candidate)
                report[candidate.category] += 1
                if not dry_run:
                    blocks_to_remove.append(block)
                else:
                    blocks_to_keep.append(block)  # Keep all in dry-run
        else:
            blocks_to_keep.append(block)
            report['kept'] += 1
    
    # Reconstruct text
    if dry_run:
        processed_text = text  # No changes in dry-run
    else:
        processed_text = '\n\n'.join(blocks_to_keep)
    
    report['total_blocks'] = total_blocks
    report['blocks_to_remove'] = len([c for c in candidates if not (c.position == 'middle' and c.confidence < 0.95)])
    report['blocks_to_keep'] = total_blocks - report['blocks_to_remove']
    report['by_category'] = defaultdict(int)
    
    for candidate in candidates:
        if not (candidate.position == 'middle' and candidate.confidence < 0.95):
            report['by_category'][candidate.category] += 1
    
    return processed_text, candidates, dict(report)


def format_dry_run_table(candidates: List[BlockCandidate]) -> str:
    """
    Format candidates as a readable table for dry-run output.
    """
    if not candidates:
        return "No blocks detected for scrubbing."
    
    lines = []
    lines.append("\n" + "="*80)
    lines.append("SCRUBBER DRY-RUN - Candidate Blocks")
    lines.append("="*80)
    lines.append(f"{'ID':<5} {'Category':<20} {'Position':<12} {'Confidence':<10} {'Reason'}")
    lines.append("-"*80)
    
    for candidate in candidates:
        reason_short = candidate.reason[:40] + "..." if len(candidate.reason) > 40 else candidate.reason
        lines.append(
            f"{candidate.block_id:<5} {candidate.category:<20} {candidate.position:<12} "
            f"{candidate.confidence:<10.2f} {reason_short}"
        )
    
    lines.append("-"*80)
    lines.append(f"Total candidates: {len(candidates)}")
    lines.append("="*80 + "\n")
    
    return "\n".join(lines)


def main():
    """CLI interface for scrubber testing."""
    import argparse
    from pathlib import Path
    from . import config as cfg_module
    
    parser = argparse.ArgumentParser(
        description='Scrub boilerplate blocks from Markdown files'
    )
    parser.add_argument('input_file', type=Path, help='Input Markdown file')
    parser.add_argument('-o', '--output', type=Path, help='Output file path')
    parser.add_argument('-c', '--config', type=Path, help='Configuration YAML file')
    parser.add_argument('--dry-run', action='store_true', help='Show candidates without removing')
    parser.add_argument('--report', action='store_true', help='Print scrubbing report')
    
    args = parser.parse_args()
    
    # Load configuration
    cfg = cfg_module.load_config(args.config) if args.config else cfg_module.load_config()
    scrubber_config = cfg.get('scrubber', {})
    
    # Read input
    input_path = args.input_file
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    md_content = input_path.read_text(encoding='utf-8')
    
    # Process
    processed_text, candidates, report = scrub_text(md_content, scrubber_config, dry_run=args.dry_run)
    
    # Output
    if args.dry_run:
        print(format_dry_run_table(candidates))
        if args.report:
            print("\nReport:")
            for key, count in sorted(report.items()):
                print(f"  {key}: {count}")
    else:
        # Determine output path
        output_path = args.output
        if not output_path:
            output_path = input_path.parent / '.tmp' / 'scrubbed_out.md'
        
        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(processed_text, encoding='utf-8')
        
        print(f"Processing: {input_path}")
        if report:
            print("\nScrubbing summary:")
            for key, count in sorted(report.items()):
                print(f"  {key}: {count}")
        print(f"\nOutput saved: {output_path}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
