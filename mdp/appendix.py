#!/usr/bin/env python3
"""
Appendix generation for scrubbed blocks.

Collects removed blocks and formats them into an Appendix.md file
with proper headers and organization.
"""

from typing import List, Dict
from pathlib import Path
from .scrubber import BlockCandidate


CATEGORY_HEADERS = {
    'authors_note': "## Removed Author's Notes",
    'translators_note': "## Removed Translator's Notes",
    'editors_note': "## Removed Editor's Notes",
    'navigation': "## Removed Navigation Text",
    'promo_ad_social': "## Removed Promotional Content",
    'watermark': "## Removed Watermarks",
    'link_farm': "## Removed Link Collections",
}


def format_appendix(candidates: List[BlockCandidate], source_file: str = "document") -> str:
    """
    Format scrubbed blocks into an Appendix document.
    
    Args:
        candidates: List of BlockCandidate objects that were removed
        source_file: Name of the source document
    
    Returns:
        Formatted Appendix.md content
    """
    if not candidates:
        return ""
    
    lines = []
    lines.append(f"# Appendix - Removed Blocks from {source_file}")
    lines.append("")
    lines.append("This appendix contains blocks that were automatically removed during scrubbing.")
    lines.append("They are preserved here for reference and can be manually restored if needed.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Group candidates by category
    by_category: Dict[str, List[BlockCandidate]] = {}
    for candidate in candidates:
        category = candidate.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(candidate)
    
    # Output each category
    for category in sorted(by_category.keys()):
        header = CATEGORY_HEADERS.get(category, f"## Removed {category.replace('_', ' ').title()}")
        lines.append(header)
        lines.append("")
        
        for candidate in by_category[category]:
            lines.append(f"### Block {candidate.block_id} ({candidate.position})")
            lines.append("")
            lines.append(f"**Reason:** {candidate.reason}")
            lines.append("")
            lines.append("**Content:**")
            lines.append("")
            lines.append(candidate.content)
            lines.append("")
            lines.append("---")
            lines.append("")
    
    return "\n".join(lines)


def write_appendix(candidates: List[BlockCandidate], appendix_path: Path, 
                   source_file: str = "document") -> None:
    """
    Write appendix to file.
    
    Args:
        candidates: List of removed blocks
        appendix_path: Path to write Appendix.md
        source_file: Name of source document
    """
    if not candidates:
        print("No blocks to write to appendix.")
        return
    
    content = format_appendix(candidates, source_file)
    
    # Ensure parent directory exists
    appendix_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    appendix_path.write_text(content, encoding='utf-8')
    print(f"Appendix written: {appendix_path} ({len(candidates)} blocks)")


def append_to_existing(candidates: List[BlockCandidate], appendix_path: Path,
                       source_file: str = "document") -> None:
    """
    Append to existing appendix file instead of overwriting.
    
    Args:
        candidates: List of removed blocks
        appendix_path: Path to Appendix.md
        source_file: Name of source document
    """
    if not candidates:
        return
    
    new_content = format_appendix(candidates, source_file)
    
    if appendix_path.exists():
        existing_content = appendix_path.read_text(encoding='utf-8')
        combined = existing_content + "\n\n" + new_content
        appendix_path.write_text(combined, encoding='utf-8')
        print(f"Appended to existing appendix: {appendix_path}")
    else:
        write_appendix(candidates, appendix_path, source_file)
