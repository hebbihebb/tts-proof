#!/usr/bin/env python3
"""
report/pretty.py - Human-Readable Report Formatter

Formats JSON report data into compact, readable tables for CLI output.
"""

from typing import Dict, Any, List
from pathlib import Path


def _truncate_path(path: str, max_len: int = 60) -> str:
    """
    Truncate a file path to fit display width.
    
    Args:
        path: File path to truncate
        max_len: Maximum length
    
    Returns:
        Truncated path with ellipsis if needed
    """
    if len(path) <= max_len:
        return path
    
    # Try to keep filename and some parent directories
    parts = Path(path).parts
    if len(parts) == 1:
        # Single component, truncate middle
        if len(path) > max_len:
            keep = (max_len - 3) // 2
            return path[:keep] + "..." + path[-keep:]
        return path
    
    # Multiple components - keep filename and truncate path
    filename = parts[-1]
    if len(filename) > max_len - 10:
        # Filename too long
        return "..." + filename[-(max_len - 3):]
    
    # Build path backwards until we hit limit
    result = filename
    for part in reversed(parts[:-1]):
        test = part + "/" + result
        if len(test) > max_len - 3:
            return "..." + result
        result = test
    
    return result


def _format_percentage(value: float) -> str:
    """Format float as percentage with sign."""
    if value >= 0:
        return f"+{value:.2%}"
    return f"{value:.2%}"


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"


def _render_section_header(title: str, width: int = 100) -> str:
    """Render a section header with border."""
    border = "=" * width
    padding = (width - len(title) - 2) // 2
    header = f"{' ' * padding} {title} {' ' * padding}"
    if len(header) < width:
        header += " " * (width - len(header))
    return f"\n{border}\n{header}\n{border}"


def _render_kv_table(items: List[tuple], indent: str = "  ") -> str:
    """Render key-value pairs as aligned table."""
    if not items:
        return ""
    
    # Find max key length
    max_key_len = max(len(str(k)) for k, v in items)
    
    lines = []
    for key, value in items:
        lines.append(f"{indent}{str(key):<{max_key_len}} : {value}")
    
    return "\n".join(lines)


def _render_rejections_table(rejections: Dict[str, int], indent: str = "  ") -> str:
    """Render rejections as compact table."""
    if not rejections or all(v == 0 for v in rejections.values()):
        return f"{indent}(none)"
    
    # Filter zero values
    non_zero = {k: v for k, v in rejections.items() if v > 0}
    if not non_zero:
        return f"{indent}(none)"
    
    # Find max key length
    max_key_len = max(len(k) for k in non_zero.keys())
    
    lines = []
    for key, count in sorted(non_zero.items(), key=lambda x: -x[1]):
        lines.append(f"{indent}{key:<{max_key_len}} : {count:>4}")
    
    return "\n".join(lines)


def render_pretty(report: Dict[str, Any]) -> str:
    """
    Render a JSON report as human-readable text.
    
    Args:
        report: Report dictionary with structure:
            {
                'input_file': str,
                'output_file': str | None,
                'steps': List[str],
                'statistics': Dict[str, Any]
            }
    
    Returns:
        Formatted report string
    """
    sections = []
    stats = report.get('statistics', {})
    
    # Section 1: Run Summary
    sections.append(_render_section_header("RUN SUMMARY"))
    
    summary_items = [
        ("Input file", _truncate_path(report.get('input_file', 'unknown'))),
        ("Output file", _truncate_path(report.get('output_file', 'stdout')) if report.get('output_file') else "stdout"),
        ("Pipeline steps", " -> ".join(report.get('steps', []))),
    ]
    
    sections.append(_render_kv_table(summary_items))
    
    # Section 2: Phase Statistics
    if stats:
        sections.append(_render_section_header("PHASE STATISTICS"))
        
        # Collect phase info
        phase_info = []
        
        # Mask phase
        if 'mask' in stats:
            mask_stats = stats['mask']
            phase_info.append(("Mask", f"{mask_stats.get('masks_created', 0)} regions masked"))
        
        # Prepass phases
        if 'prepass-basic' in stats:
            pb_stats = stats['prepass-basic']
            changes = sum(pb_stats.get(k, 0) for k in ['control_chars_stripped', 'spaced_words_joined', 'hyphenation_healed'])
            phase_info.append(("Prepass Basic", f"{changes} normalizations"))
        
        if 'prepass-advanced' in stats:
            pa_stats = stats['prepass-advanced']
            changes = sum(pa_stats.get(k, 0) for k in ['casing_fixes', 'punctuation_fixes', 'ellipsis_fixes'])
            phase_info.append(("Prepass Advanced", f"{changes} normalizations"))
        
        # Scrubber
        if 'scrubber' in stats:
            scrub_stats = stats['scrubber']
            blocks = scrub_stats.get('blocks_removed', 0)
            phase_info.append(("Scrubber", f"{blocks} blocks removed"))
        
        # Grammar
        if 'grammar' in stats:
            gram_stats = stats['grammar']
            fixes = gram_stats.get('corrections_applied', 0)
            phase_info.append(("Grammar", f"{fixes} corrections"))
        
        # Detector
        if 'detect' in stats:
            det_stats = stats['detect']
            suggestions = det_stats.get('suggestions_valid', 0)
            phase_info.append(("Detector", f"{suggestions} suggestions (model: {det_stats.get('model', 'unknown')})"))
        
        # Apply
        if 'apply' in stats:
            app_stats = stats['apply']
            applied = app_stats.get('replacements_applied', 0)
            nodes = app_stats.get('nodes_changed', 0)
            phase_info.append(("Apply", f"{applied} replacements in {nodes} nodes"))
        
        # Fixer
        if 'fix' in stats:
            fix_stats = stats['fix']
            fixed = fix_stats.get('spans_fixed', 0)
            total = fix_stats.get('spans_total', 0)
            phase_info.append(("Fixer", f"{fixed}/{total} spans (model: {fix_stats.get('model', 'unknown')})"))
        
        if phase_info:
            sections.append(_render_kv_table(phase_info))
    
    # Section 3: Rejections (if any phase has rejections)
    rejection_sections = []
    
    if 'detect' in stats and stats['detect'].get('rejections'):
        rejection_sections.append(("Detector Rejections", stats['detect']['rejections']))
    
    if 'fix' in stats and stats['fix'].get('rejections'):
        rejection_sections.append(("Fixer Rejections", stats['fix']['rejections']))
    
    if rejection_sections:
        sections.append(_render_section_header("REJECTIONS"))
        for title, rejections in rejection_sections:
            sections.append(f"\n{title}:")
            sections.append(_render_rejections_table(rejections))
    
    # Section 4: Growth Analysis (if apply or fix was run)
    growth_data = []
    
    if 'apply' in stats:
        app_stats = stats['apply']
        ratio = app_stats.get('growth_ratio', 0.0)
        delta = app_stats.get('length_delta', 0)
        growth_data.append(("Apply phase", f"{_format_percentage(ratio)} ({delta:+d} chars)"))
    
    if 'fix' in stats:
        fix_stats = stats['fix']
        ratio = fix_stats.get('file_growth_ratio', 0.0)
        growth_data.append(("Fixer phase", f"{_format_percentage(ratio)}"))
    
    if growth_data:
        sections.append(_render_section_header("FILE GROWTH"))
        sections.append(_render_kv_table(growth_data))
    
    # Section 5: Quality Flags
    quality_flags = []
    
    # Determinism flag from detector or fixer
    if 'detect' in stats and 'deterministic' in stats['detect']:
        if stats['detect']['deterministic']:
            quality_flags.append(("Detector", "Deterministic (seed set)"))
        else:
            quality_flags.append(("Detector", "Non-deterministic"))
    
    if 'fix' in stats and 'deterministic' in stats['fix']:
        if stats['fix']['deterministic']:
            quality_flags.append(("Fixer", "Deterministic (seed set)"))
        else:
            quality_flags.append(("Fixer", "Non-deterministic"))
    
    if quality_flags:
        sections.append(_render_section_header("QUALITY FLAGS"))
        sections.append(_render_kv_table(quality_flags))
    
    # Section 6: Artifacts
    artifact_items = []
    
    if report.get('output_file'):
        artifact_items.append(("Output file", _truncate_path(report['output_file'])))
    
    # Plan file (if detector was run)
    # Note: This is inferred, not in report structure - would need to be added
    
    if artifact_items:
        sections.append(_render_section_header("ARTIFACTS"))
        sections.append(_render_kv_table(artifact_items))
    
    # Combine all sections
    return "\n".join(sections) + "\n"
