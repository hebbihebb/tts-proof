import pytest
from pathlib import Path
from mdp import markdown_adapter
from mdp.markdown_adapter import _get_protected_spans

TEST_DATA_DIR = Path(__file__).parent.parent / "test_data" / "ast"
FIXTURES = [
    "fences_inline.md",
    "links_images.md",
    "tables_lists.md",
    "html_blocks.md",
    "math_footnotes.md",
]

@pytest.mark.parametrize("fixture_file", FIXTURES)
def test_round_trip_identity(fixture_file):
    """Tests that masking and then unmasking results in the original content."""
    original_md = (TEST_DATA_DIR / fixture_file).read_text(encoding="utf-8")
    masked_md, mask_table = markdown_adapter.mask_protected(original_md)
    unmasked_md = markdown_adapter.unmask(masked_md, mask_table)
    assert unmasked_md == original_md, f"Round-trip failed for {fixture_file}"

@pytest.mark.parametrize("fixture_file, expected_texts, unexpected_texts", [
    ("fences_inline.md", ["This is some"], ["def hello_world", "console.log", "inline code"]),
    ("links_images.md", ["A link to a website", "An image"], ["https://www.example.com", "image.jpg", "https://www.google.com"]),
    ("tables_lists.md", ["Header 1", "Header 2", "Cell 1", "Cell 2", "Cell 3", "Cell 4", "Item 1", "Sub-item 1.1", "Sub-item 1.2", "Item 2"], []),
    ("html_blocks.md", [], ["<summary>Click to expand</summary>", "<p>This is a paragraph inside a div.</p>"]),
    ("math_footnotes.md", ["This is a footnote", "This is the footnote definition.", "This is some inline math:", "This is a block of math:"], ["E = mc^2", r"\int_0^\infty"]),
])
def test_extract_text_spans_content(fixture_file, expected_texts, unexpected_texts):
    """Tests that `extract_text_spans` correctly identifies text and excludes protected content."""
    md_content = (TEST_DATA_DIR / fixture_file).read_text(encoding="utf-8")
    text_spans = markdown_adapter.extract_text_spans(md_content)
    extracted_text = "".join(span['text'] for span in text_spans)

    for text in expected_texts:
        assert text in extracted_text, f"Expected text '{text}' not found in {fixture_file}"

    for text in unexpected_texts:
        assert text not in extracted_text, f"Unexpected text '{text}' found in {fixture_file}"

def get_all_text_spans(md: str) -> list[dict]:
    """A helper that is a direct copy of the internal implementation of extract_text_spans
    but without the final filtering step. This is needed for the reconstruction test."""
    protected_spans = _get_protected_spans(md)
    text_spans = []
    last_end = 0
    protected_spans.sort(key=lambda s: s['start'])

    for span in protected_spans:
        start, end = span['start'], span['end']
        if start > last_end:
            text_segment = md[last_end:start]
            if text_segment:
                text_spans.append({"start": last_end, "end": start, "type": "TEXT", "text": text_segment})
        last_end = max(last_end, end)

    if last_end < len(md):
        text_segment = md[last_end:]
        if text_segment:
            text_spans.append({"start": last_end, "end": len(md), "type": "TEXT", "text": text_segment})
    return text_spans

def test_reconstruction_from_spans():
    """
    Tests that the original document can be perfectly reconstructed by combining
    all text spans (including whitespace) and protected spans.
    """
    for fixture_file in FIXTURES:
        original_md = (TEST_DATA_DIR / fixture_file).read_text(encoding="utf-8")

        protected_spans = _get_protected_spans(original_md)
        # Use our internal helper to get all text spans, including whitespace-only ones
        text_spans = get_all_text_spans(original_md)

        all_spans = sorted(protected_spans + text_spans, key=lambda s: s['start'])

        last_end = 0
        for span in all_spans:
            assert span['start'] == last_end, f"Gap or overlap at index {last_end} in {fixture_file}"
            last_end = span['end']

        assert last_end == len(original_md), f"Spans do not cover the entire document in {fixture_file}"

        reconstructed_md = "".join(span['text'] for span in all_spans)
        assert reconstructed_md == original_md, f"Reconstruction failed for {fixture_file}"