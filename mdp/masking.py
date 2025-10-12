import re
from collections import defaultdict

SENTINEL_PATTERN = re.compile(r"\{\{MASK_([A-Z_]+)_(\d+)\}\}")

def create_sentinel(mask_type, index):
    """Creates a unique sentinel for a given mask type and index."""
    return f"{{{{MASK_{mask_type}_{index}}}}}"

def get_mask_table_and_masked_content(content, protected_spans):
    """
    Generates a masked version of the content and a table mapping sentinels to the original text.
    """
    mask_table = {}
    masked_content = []
    last_end = 0
    counts = defaultdict(int)

    protected_spans.sort(key=lambda s: s['start'])

    for span in protected_spans:
        start, end, span_type, text = span['start'], span['end'], span['type'], span['text']

        if start < last_end:
            # Skip overlapping spans, which can be produced by regex patterns
            continue

        masked_content.append(content[last_end:start])

        index = counts[span_type]
        sentinel = create_sentinel(span_type.upper(), index)
        mask_table[sentinel] = text

        masked_content.append(sentinel)

        counts[span_type] += 1
        last_end = end

    masked_content.append(content[last_end:])

    return "".join(masked_content), mask_table

def unmask(masked_content, mask_table):
    """
    Restores the original content by replacing sentinels with their original text.
    """
    if not mask_table:
        return masked_content

    sorted_sentinels = sorted(mask_table.keys(), key=len, reverse=True)

    sentinel_pattern = re.compile("|".join(re.escape(s) for s in sorted_sentinels))

    def replace_match(match):
        return mask_table[match.group(0)]

    return sentinel_pattern.sub(replace_match, masked_content)