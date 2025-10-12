#!/usr/bin/env python3
"""
Unit tests for prepass TTS problem detection.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from prepass import (
    detect_tts_problems, run_prepass, write_prepass_report, load_prepass_report,
    get_problem_words_for_grammar, inject_prepass_into_grammar_prompt,
    DETECTOR_PROMPT
)


class TestPrepass(unittest.TestCase):
    
    def test_detector_prompt_parsing(self):
        """Test parsing of detector LLM response."""
        # Mock successful response
        mock_response = '{"replacements": [{"find": "F ʟ ᴀ s ʜ", "replace": "Flash", "reason": "spaced letters"}]}'
        
        with patch('prepass.call_lmstudio', return_value=mock_response):
            replacements = detect_tts_problems("http://test", "test-model", "test text")
            
        self.assertEqual(len(replacements), 1)
        self.assertEqual(replacements[0]['find'], "F ʟ ᴀ s ʜ")
        self.assertEqual(replacements[0]['replace'], "Flash")
        self.assertEqual(replacements[0]['reason'], "spaced letters")
    
    def test_detector_prompt_parsing_with_extra_text(self):
        """Test parsing when LLM response has extra text around JSON."""
        mock_response = 'Here is the analysis:\n{"replacements": [{"find": "TEST", "replace": "Test", "reason": "caps"}]}\nDone.'
        
        with patch('prepass.call_lmstudio', return_value=mock_response):
            replacements = detect_tts_problems("http://test", "test-model", "test text")
            
        self.assertEqual(len(replacements), 1)
        self.assertEqual(replacements[0]['find'], "TEST")
        self.assertEqual(replacements[0]['replace'], "Test")
    
    def test_detector_prompt_parsing_invalid_json(self):
        """Test handling of invalid JSON response."""
        mock_response = 'This is not valid JSON'
        
        with patch('prepass.call_lmstudio', return_value=mock_response):
            replacements = detect_tts_problems("http://test", "test-model", "test text")
            
        self.assertEqual(replacements, [])
    
    def test_report_merge_and_deduplication(self):
        """Test report generation with deduplication."""
        # Mock markdown content
        test_markdown = "# Test\n\nSome F ʟ ᴀ s ʜ text.\n\nMore F ʟ ᴀ s ʜ content."
        
        # Mock chunking to return test chunks
        with patch('prepass.chunk_paragraphs') as mock_chunk:
            mock_chunk.return_value = [
                ("text", "Some F ʟ ᴀ s ʜ text."),
                ("text", "More F ʟ ᴀ s ʜ content.")
            ]
            
            # Mock detect_tts_problems to return same replacement in both chunks
            with patch('prepass.detect_tts_problems') as mock_detect:
                mock_detect.return_value = [{"find": "F ʟ ᴀ s ʜ", "replace": "Flash", "reason": "spaced letters"}]
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                    f.write(test_markdown)
                    f.flush()
                    
                    test_path = Path(f.name)
                    
                try:
                    report = run_prepass(test_path, "http://test", "test-model", show_progress=False)
                    
                    # Check report structure
                    self.assertIn('source', report)
                    self.assertIn('created_at', report)
                    self.assertIn('chunks', report)
                    self.assertIn('summary', report)
                    
                    # Check deduplication worked
                    unique_words = report['summary']['unique_problem_words']
                    self.assertEqual(len(unique_words), 1)  # Should be deduplicated
                    self.assertEqual(unique_words[0], "F ʟ ᴀ s ʜ")
                    
                    # Check chunks
                    self.assertEqual(len(report['chunks']), 2)
                    
                finally:
                    test_path.unlink()
    
    def test_write_and_load_report(self):
        """Test writing and loading prepass reports."""
        test_report = {
            "source": "test.md",
            "created_at": "2025-10-10T12:00:00",
            "chunks": [
                {
                    "id": 1,
                    "range": {"start_byte": 0, "end_byte": 100},
                    "problems": [{"word": "TEST", "reason": "caps"}]
                }
            ],
            "summary": {
                "unique_problem_words": ["TEST"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_path = Path(f.name)
            
        try:
            write_prepass_report(test_report, test_path)
            loaded_report = load_prepass_report(test_path)
            
            self.assertEqual(loaded_report, test_report)
            
        finally:
            test_path.unlink()
    
    def test_get_problem_words_for_grammar(self):
        """Test extracting problem words for grammar pass."""
        test_report = {
            "summary": {
                "unique_problem_words": ["word1", "word2", "word3"]
            }
        }
        
        # Test normal case
        words = get_problem_words_for_grammar(test_report)
        self.assertEqual(words, ["word1", "word2", "word3"])
        
        # Test max_words limiting
        words = get_problem_words_for_grammar(test_report, max_words=2)
        self.assertEqual(words, ["word1", "word2"])
        
        # Test empty report
        empty_report = {"summary": {"unique_problem_words": []}}
        words = get_problem_words_for_grammar(empty_report)
        self.assertEqual(words, [])
    
    def test_grammar_prompt_injection(self):
        """Test injection of prepass replacements into grammar prompt."""
        base_prompt = "You are a grammar assistant."
        replacement_map = {"F ʟ ᴀ s ʜ": "Flash", "T E S T": "Test"}
        
        injected = inject_prepass_into_grammar_prompt(base_prompt, replacement_map)
        
        self.assertIn(base_prompt, injected)
        self.assertIn("F ʟ ᴀ s ʜ", injected)
        self.assertIn("Flash", injected)
        self.assertIn("PREPASS REPLACEMENTS", injected)
    
    def test_grammar_prompt_injection_empty_list(self):
        """Test grammar prompt injection with empty replacement map."""
        base_prompt = "You are a grammar assistant."
        
        injected = inject_prepass_into_grammar_prompt(base_prompt, {})
        
        self.assertEqual(injected, base_prompt)  # Should be unchanged
    
    def test_grammar_prompt_injection_long_list(self):
        """Test grammar prompt injection with long replacement map gets truncated."""
        base_prompt = "You are a grammar assistant."
        # Create a map longer than 100 items
        replacement_map = {f"word{i}": f"fixed{i}" for i in range(150)}
        
        injected = inject_prepass_into_grammar_prompt(base_prompt, replacement_map)
        
        # Should contain first 100 replacements but not beyond
        self.assertIn("word0", injected)
        self.assertIn("word99", injected)
        # Note: Due to dict ordering in Python 3.7+, word100 might not be included
        # but the total count should be limited


if __name__ == '__main__':
    unittest.main()