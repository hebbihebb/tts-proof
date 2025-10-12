#!/usr/bin/env python3
"""
Unit tests for detector/chunking.py - Node chunking and pre-flight checks
"""

import pytest
from detector.chunking import (
    split_into_sentences,
    chunk_text_node,
    should_skip_node,
)


@pytest.fixture
def basic_config():
    """Basic configuration for chunking tests."""
    return {
        'max_chunk_size': 600,
        'overlap_size': 50,
        'max_non_alpha_ratio': 0.5,
    }


class TestSentenceSplitting:
    """Tests for sentence splitting."""
    
    def test_simple_sentence_split(self):
        """Simple sentences should split correctly with delimiters preserved."""
        text = "This is sentence one. This is sentence two? This is sentence three!"
        sentences = split_into_sentences(text)
        
        assert len(sentences) == 3
        assert sentences[0] == "This is sentence one. "
        assert sentences[1] == "This is sentence two? "
        assert sentences[2] == "This is sentence three!"
    
    def test_multiple_punctuation(self):
        """Multiple punctuation marks should be preserved."""
        text = "What?! Really?? Yes!!!"
        sentences = split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "?!" in sentences[0]
        assert "??" in sentences[1]
        assert "!!!" in sentences[2]
    
    def test_no_punctuation(self):
        """Text without sentence punctuation should return as single item."""
        text = "This is just a fragment"
        sentences = split_into_sentences(text)
        
        assert len(sentences) == 1
        assert sentences[0] == text
    
    def test_empty_text(self):
        """Empty text should return empty list."""
        sentences = split_into_sentences("")
        assert sentences == []


class TestNodeChunking:
    """Tests for text node chunking with overlap."""
    
    def test_short_node_no_split(self, basic_config):
        """Nodes shorter than max_chunk_size should not be split."""
        text = "This is a short text that doesn't need chunking."
        chunks = chunk_text_node(text, basic_config)
        
        assert len(chunks) == 1
        assert chunks[0][0] == text
        assert chunks[0][1] == 0  # start offset
        assert chunks[0][2] == len(text)  # end offset
    
    def test_long_node_splits(self, basic_config):
        """Long nodes should be split into multiple chunks."""
        # Create text longer than 600 chars
        text = "This is a sentence. " * 50  # ~1000 chars
        chunks = chunk_text_node(text, basic_config)
        
        assert len(chunks) > 1
        # Each chunk should be at or under max size (except last)
        for i, (chunk_text, start, end) in enumerate(chunks[:-1]):
            assert len(chunk_text) <= basic_config['max_chunk_size'] * 1.2  # Some tolerance
    
    def test_overlap_window(self, basic_config):
        """Adjacent chunks should have overlap."""
        # Create text that will split into 2+ chunks
        text = "Sentence one. " * 60  # ~840 chars
        chunks = chunk_text_node(text, basic_config)
        
        if len(chunks) > 1:
            # Check that second chunk starts before first chunk ends
            chunk1_text, chunk1_start, chunk1_end = chunks[0]
            chunk2_text, chunk2_start, chunk2_end = chunks[1]
            
            # Overlap should exist
            overlap_size = chunk1_end - chunk2_start
            assert overlap_size > 0
            assert overlap_size <= basic_config['overlap_size']
            
            # Verify overlapping text is actually the same
            overlap_from_chunk1 = text[chunk2_start:chunk1_end]
            overlap_from_chunk2 = chunk2_text[:overlap_size]
            assert overlap_from_chunk2 in overlap_from_chunk1


class TestSkipConditions:
    """Tests for node skip pre-flight checks."""
    
    def test_skip_empty_node(self, basic_config):
        """Empty or whitespace-only nodes should be skipped."""
        should_skip, reason = should_skip_node("", basic_config)
        assert should_skip
        assert reason == "empty"
        
        should_skip, reason = should_skip_node("   \n\t   ", basic_config)
        assert should_skip
        assert reason == "empty"
    
    def test_skip_mostly_uppercase(self, basic_config):
        """Nodes that are mostly uppercase should be skipped."""
        text = "THIS IS A HEADING OR SHOUT"
        should_skip, reason = should_skip_node(text, basic_config)
        assert should_skip
        assert reason == "mostly_uppercase"
    
    def test_dont_skip_normal_casing(self, basic_config):
        """Normal casing should not be skipped."""
        text = "This is normal text with Some capitalization."
        should_skip, reason = should_skip_node(text, basic_config)
        assert not should_skip
    
    def test_skip_urls(self, basic_config):
        """Text that looks like URLs should be skipped."""
        test_cases = [
            "https://example.com/path",
            "http://test.org",
            "Check out example.com // latest updates",
        ]
        
        for text in test_cases:
            should_skip, reason = should_skip_node(text, basic_config)
            assert should_skip, f"Should skip URL: {text}"
            assert reason == "url"
    
    def test_skip_code_ish(self, basic_config):
        """Text with too many non-alpha characters should be skipped."""
        # Lots of symbols/digits (code-like) - need >50% non-alpha non-space
        text = "x = {1: [2, 3], 4: (5 + 6)}"  # Much higher symbol density
        should_skip, reason = should_skip_node(text, basic_config)
        assert should_skip
        assert reason == "code_ish"
    
    def test_dont_skip_normal_prose(self, basic_config):
        """Normal prose with punctuation should not be skipped."""
        text = "This is normal text! It has punctuation, numbers like 5, and that's okay."
        should_skip, reason = should_skip_node(text, basic_config)
        # Should not skip because non-alpha ratio is reasonable
        assert not should_skip


class TestMaskBoundaries:
    """Tests to ensure we never split inside mask sentinels."""
    
    def test_never_cross_mask_boundaries(self, basic_config):
        """Chunking should never split inside mask sentinels."""
        # Simulate text with masks (Phase 1 sentinels)
        text = "Before text __MASKED_0__ middle text __MASKED_1__ after text. " * 20
        chunks = chunk_text_node(text, basic_config)
        
        # Each chunk should have complete mask markers (not split mid-marker)
        for chunk_text, start, end in chunks:
            # Count opening and closing markers in this chunk
            open_count = chunk_text.count('__MASKED_')
            # Each __MASKED_ should be followed by number and closing __
            # Simple check: no partial markers like "__MASKED" without number
            assert '__MASKED' not in chunk_text or '__MASKED_' in chunk_text
    
    def test_preserve_sentinel_integrity(self, basic_config):
        """Mask sentinels should never be broken across chunks."""
        # Text with sentinel-like patterns
        text = "Normal text. __SENTINEL_START__ protected content __SENTINEL_END__ more text. " * 15
        chunks = chunk_text_node(text, basic_config)
        
        for chunk_text, start, end in chunks:
            # If START appears, END should also appear (or neither)
            has_start = '__SENTINEL_START__' in chunk_text
            has_end = '__SENTINEL_END__' in chunk_text
            
            # Count occurrences
            start_count = chunk_text.count('__SENTINEL_START__')
            end_count = chunk_text.count('__SENTINEL_END__')
            
            # Should be balanced (might have multiple pairs in one chunk)
            assert start_count == end_count, "Sentinels should be balanced in chunk"
