import logging
import re
from collections import defaultdict

from . import masking

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ESCAPED_BACKTICK_PLACEHOLDER = "___ESCAPED_BACKTICK_PLACEHOLDER___"

try:
    import mistletoe
    _mistletoe_available = True
except ImportError:
    _mistletoe_available = False
    logging.warning("mistletoe library not found. Falling back to regex-based parsing.")

def _get_protected_spans_regex(md: str) -> list[dict]:
    """Fallback function to find protected spans using regular expressions."""
    spans = []

    md_no_escapes = md.replace(r'\\`', ESCAPED_BACKTICK_PLACEHOLDER)

    patterns = {
        # Match fenced code blocks, including the final newline to avoid gaps
        "CODE_FENCE": r"(?s)(^```[a-zA-Z]*\n.*?^```\s*?$|^~~~[a-zA-Z]*\n.*?^~~~\s*?$)",
        "INLINE_CODE": r"`+.+?`+",
        "HTML_BLOCK": r"(?s)<(details|div|table).*?</\1>",
        "LINK_URL": r"\[[^\]]*\]\(([^)]+)\)",
        "IMAGE_URL": r"!\[[^\]]*\]\(([^)]+)\)",
        "AUTOLINK": r"<https?://[^>]+>",
        "MATH_BLOCK": r"(?s)\$\$.*?\$\$",
        "INLINE_MATH": r"(?<!\\)\$.*?(?<!\\)\$", # Avoid matching escaped dollars
    }

    for span_type, pattern in patterns.items():
        for match in re.finditer(pattern, md_no_escapes, re.MULTILINE):
            if match.group(0):
                if span_type in ["LINK_URL", "IMAGE_URL"]:
                     start, end = match.start(1), match.end(1)
                else:
                    start, end = match.start(0), match.end(0)

                spans.append({
                    "start": start,
                    "end": end,
                    "type": span_type,
                    "text": md[start:end].replace(ESCAPED_BACKTICK_PLACEHOLDER, r'\\`')
                })

    spans.sort(key=lambda s: s['start'])

    if not spans:
        return []

    # Filter out overlapping spans by keeping the one that comes first
    non_overlapping_spans = [spans[0]]
    for current_span in spans[1:]:
        last_span = non_overlapping_spans[-1]
        if current_span['start'] >= last_span['end']:
            non_overlapping_spans.append(current_span)

    return non_overlapping_spans

def _get_protected_spans(md: str) -> list[dict]:
    """Main function to get protected spans using a regex-based approach."""
    if _mistletoe_available:
        logging.info("Mistletoe is available, but regex is used for reliable byte offsets.")
    return _get_protected_spans_regex(md)

def mask_protected(md: str) -> tuple[str, dict]:
    """Masks protected regions of a Markdown string with stable sentinels."""
    protected_spans = _get_protected_spans(md)

    masked_md, mask_table = masking.get_mask_table_and_masked_content(md, protected_spans)

    summary = defaultdict(int)
    for span in protected_spans:
        summary[span['type']] += 1
    logging.info(f"Masking complete. Found and masked: {dict(summary)}")

    return masked_md, mask_table

def unmask(masked_md: str, mask_table: dict) -> str:
    """Restores a masked Markdown string by replacing sentinels with their original content."""
    return masking.unmask(masked_md, mask_table)

def extract_text_spans(md: str) -> list[dict]:
    """Extracts spans of text that are safe to modify, including whitespace."""
    protected_spans = _get_protected_spans(md)

    text_spans = []
    last_end = 0

    protected_spans.sort(key=lambda s: s['start'])

    for span in protected_spans:
        start, end = span['start'], span['end']

        if start > last_end:
            text_segment = md[last_end:start]
            # Include all segments, even if they are just whitespace, to allow perfect reconstruction
            if text_segment:
                text_spans.append({
                    "start": last_end,
                    "end": start,
                    "type": "TEXT",
                    "text": text_segment
                })

        last_end = max(last_end, end)

    if last_end < len(md):
        text_segment = md[last_end:]
        if text_segment:
            text_spans.append({
                "start": last_end,
                "end": len(md),
                "type": "TEXT",
                "text": text_segment
            })

    # A second pass to filter out the text spans that are only whitespace for the caller,
    # but we still need them for the reconstruction test.
    # The primary function should return only meaningful text.
    return [span for span in text_spans if span['text'].strip()]