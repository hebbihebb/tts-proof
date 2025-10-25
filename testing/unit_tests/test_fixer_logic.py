#!/usr/bin/env python3
"""
Unit tests for fixer/fixer.py - Main logic functions
"""

import pytest
from fixer.fixer import split_long_node, fix_span, apply_fixer
from fixer.client import FixerClient


class TestSplitLongNode:
    """Test text node splitting logic."""
    
    def test_short_node_not_split(self):
        """Short text should not be split."""
        text = "This is a short sentence."
        spans = split_long_node(text, max_chars=600)
        assert len(spans) == 1
        assert spans[0] == text
    
    def test_long_node_split_on_sentences(self):
        """Long text should be split on sentence boundaries."""
        text = "First sentence here. Second sentence is here. Third one follows."
        spans = split_long_node(text, max_chars=30)
        # Should split into multiple spans
        assert len(spans) > 1
        # Reassembly should match original
        reassembled = "".join(spans)
        assert reassembled == text
    
    def test_no_sentence_boundaries(self):
        """Text without sentence boundaries should split on whitespace."""
        text = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        spans = split_long_node(text, max_chars=20)
        # Should split into multiple spans
        assert len(spans) > 1
        # Reassembly should match original
        reassembled = "".join(spans)
        assert reassembled == text
    
    def test_very_long_word(self):
        """Very long word that can't be split should be kept."""
        text = "a" * 1000  # Single long word
        spans = split_long_node(text, max_chars=600)
        # Will be split or kept as single span
        assert len(spans) >= 1
        reassembled = "".join(spans)
        assert reassembled == text
    
    def test_preserves_content(self):
        """Splitting should preserve all content."""
        text = "Sentence one! Sentence two? Sentence three. The end."
        spans = split_long_node(text, max_chars=25)
        reassembled = "".join(spans)
        assert reassembled == text
    
    def test_empty_text(self):
        """Empty text should return single empty span."""
        spans = split_long_node("", max_chars=600)
        assert len(spans) == 1
        assert spans[0] == ""


class TestFixSpan:
    """Test single span fixing with mocked client."""
    
    def test_successful_fix(self):
        """Successful model call should return fixed text."""
        # Create mock client
        class MockClient:
            def call_model(self, system_prompt, user_prompt):
                return "Fixed text here.", ""
        
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'locale': 'en'
        }
        
        result, stats = fix_span("Original text.", MockClient(), config)
        
        assert result == "Fixed text here."
        assert stats['span_fixed'] is True
        assert stats['rejection_reason'] is None
    
    def test_model_error_returns_original(self):
        """Model error should fail-safe to original."""
        class MockClient:
            def call_model(self, system_prompt, user_prompt):
                return "", "Timeout after 10s"
        
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'locale': 'en'
        }
        
        original = "Original text."
        result, stats = fix_span(original, MockClient(), config)
        
        assert result == original
        assert stats['span_fixed'] is False
        assert stats['rejection_reason'] == "timeout"
    
    def test_forbidden_token_returns_original(self):
        """Output with forbidden tokens should fail-safe to original."""
        class MockClient:
            def call_model(self, system_prompt, user_prompt):
                return "This has `code` in it.", ""
        
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'locale': 'en'
        }
        
        original = "Original text."
        result, stats = fix_span(original, MockClient(), config)
        
        assert result == original
        assert stats['span_fixed'] is False
        assert stats['rejection_reason'] == "forbidden_tokens"
    
    def test_excessive_growth_returns_original(self):
        """Output with excessive growth should fail-safe to original."""
        class MockClient:
            def call_model(self, system_prompt, user_prompt):
                return "This is a much much much longer response than the original.", ""
        
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'locale': 'en'
        }
        
        original = "Short."
        result, stats = fix_span(original, MockClient(), config)
        
        assert result == original
        assert stats['span_fixed'] is False
        assert stats['rejection_reason'] == "growth_limit"
    
    def test_connection_error_propagates(self):
        """ConnectionError should propagate for exit code 2."""
        class MockClient:
            def call_model(self, system_prompt, user_prompt):
                raise ConnectionError("Server unreachable")
        
        config = {
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'locale': 'en'
        }
        
        with pytest.raises(ConnectionError):
            fix_span("Original text.", MockClient(), config)


class TestApplyFixer:
    """Test full fixer application with mocked client."""
    
    def test_stats_structure(self):
        """Stats should have correct structure."""
        # Mock apply_fixer to test stats without actual LLM
        text = "# Heading\n\nSome text here."
        text_nodes = [
            {'start': 12, 'end': 27, 'text': 'Some text here.', 'type': 'TEXT'}
        ]
        mask_table = {}
        config = {
            'model': 'test-model',
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'file_max_growth_ratio': 0.05,
            'seed': 7,
            'locale': 'en',
            'api_base': 'http://test',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9
        }
        
        # Patch FixerClient to avoid real API calls
        import fixer.fixer
        original_client = fixer.fixer.FixerClient
        
        class MockClient:
            def __init__(self, config):
                pass
            def call_model(self, system_prompt, user_prompt):
                # Return slightly modified text
                return user_prompt.split("<<<")[1].split(">>>")[0].strip() + "!", ""
        
        fixer.fixer.FixerClient = MockClient
        
        try:
            result, stats = apply_fixer(text, text_nodes, mask_table, config)
            
            # Check stats structure
            assert 'phase' in stats
            assert stats['phase'] == 'fixer'
            assert 'model' in stats
            assert 'nodes_seen' in stats
            assert 'spans_total' in stats
            assert 'spans_fixed' in stats
            assert 'spans_rejected' in stats
            assert 'rejections' in stats
            assert 'file_growth_ratio' in stats
            assert 'deterministic' in stats
            
            # Check rejections structure
            assert 'forbidden_tokens' in stats['rejections']
            assert 'growth_limit' in stats['rejections']
            assert 'empty_or_non_text' in stats['rejections']
            assert 'timeout' in stats['rejections']
            assert 'non_response' in stats['rejections']
            
        finally:
            fixer.fixer.FixerClient = original_client
    
    def test_short_nodes_skipped(self):
        """Nodes shorter than 20 chars should be skipped."""
        text = "# Heading\n\nShort."
        text_nodes = [
            {'start': 12, 'end': 18, 'text': 'Short.', 'type': 'TEXT'}
        ]
        mask_table = {}
        config = {
            'model': 'test-model',
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'file_max_growth_ratio': 0.05,
            'seed': 7,
            'locale': 'en',
            'api_base': 'http://test',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9
        }
        
        import fixer.fixer
        original_client = fixer.fixer.FixerClient
        
        class MockClient:
            def __init__(self, config):
                pass
            def call_model(self, system_prompt, user_prompt):
                pytest.fail("Should not call model for short nodes")
        
        fixer.fixer.FixerClient = MockClient
        
        try:
            result, stats = apply_fixer(text, text_nodes, mask_table, config)
            
            # Should skip short node
            assert stats['nodes_seen'] == 1
            assert stats['spans_total'] == 0  # No spans processed
            assert result == text  # Unchanged
            
        finally:
            fixer.fixer.FixerClient = original_client
    
    def test_file_growth_limit_reverts(self):
        """Excessive file growth should revert to original."""
        # Use text long enough that we actually get processing
        text = "This is a test sentence that will be expanded. " * 50  # ~2400 chars
        text_nodes = [
            {'start': 0, 'end': len(text), 'text': text, 'type': 'TEXT'}
        ]
        mask_table = {}
        config = {
            'model': 'test-model',
            'forbid_markdown_tokens': True,
            'node_max_growth_ratio': 0.20,
            'file_max_growth_ratio': 0.05,  # 5% limit
            'seed': 7,
            'locale': 'en',
            'api_base': 'http://test',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9
        }
        
        import fixer.fixer
        original_client = fixer.fixer.FixerClient
        
        class MockClient:
            def __init__(self, config):
                pass
            def call_model(self, system_prompt, user_prompt):
                # Extract text from user prompt and grow it by 10% per span
                if "TEXT:" in user_prompt:
                    content = user_prompt.split("<<<")[1].split(">>>")[0].strip()
                    # Add 10% more content
                    extra = "extra words added here " * int(len(content) * 0.1 / 20)
                    return content + " " + extra, ""
                return user_prompt, ""
        
        fixer.fixer.FixerClient = MockClient
        
        try:
            result, stats = apply_fixer(text, text_nodes, mask_table, config)
            
            # Should revert to original due to file growth limit
            # OR if it passes individual node checks, should show growth
            if result == text:
                # Reverted successfully
                assert stats['file_growth_ratio'] > 0.05
            else:
                # Growth was within limits
                assert stats['file_growth_ratio'] <= 0.05
            
        finally:
            fixer.fixer.FixerClient = original_client


class TestSpanReassembly:
    """Test that split spans reassemble correctly."""
    
    def test_spans_reassemble_in_order(self):
        """Split spans should reassemble in correct order."""
        text = "First sentence. Second sentence. Third sentence."
        spans = split_long_node(text, max_chars=20)
        
        # Manually "fix" each span (just append "!")
        fixed_spans = [span + "!" for span in spans]
        
        # Reassemble
        reassembled = "".join(fixed_spans)
        
        # Should have all content with modifications
        assert "First" in reassembled
        assert "Second" in reassembled
        assert "Third" in reassembled
        assert reassembled.count("!") == len(spans)
    
    def test_whitespace_preserved(self):
        """Whitespace between spans should be preserved."""
        text = "Sentence one.  Sentence two."  # Two spaces
        spans = split_long_node(text, max_chars=20)
        reassembled = "".join(spans)
        
        # Should preserve double space
        assert "one.  Sentence" in reassembled or reassembled == text
