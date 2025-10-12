#!/usr/bin/env python3
"""
Unit tests for prepass integration in backend API.
"""

import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from prepass import inject_prepass_into_grammar_prompt, get_problem_words_for_grammar

class TestPrepassIntegration(unittest.TestCase):
    
    def test_get_problem_words_for_grammar(self):
        """Test extracting problem words from prepass report."""
        test_report = {
            "summary": {
                "unique_problem_words": ["F ʟ ᴀ s ʜ", "T E S T", "WEIRD_CAPS"]
            }
        }
        
        words = get_problem_words_for_grammar(test_report)
        self.assertEqual(words, ["F ʟ ᴀ s ʜ", "T E S T", "WEIRD_CAPS"])
    
    def test_get_problem_words_for_grammar_with_limit(self):
        """Test that problem words are limited to max_words."""
        # Create a long list of words
        long_list = [f"word{i}" for i in range(250)]
        test_report = {
            "summary": {
                "unique_problem_words": long_list
            }
        }
        
        words = get_problem_words_for_grammar(test_report, max_words=200)
        self.assertEqual(len(words), 200)
        self.assertEqual(words[:3], ["word0", "word1", "word2"])
    
    def test_inject_prepass_into_grammar_prompt(self):
        """Test injection of prepass words into grammar prompt."""
        base_prompt = "You are a grammar assistant."
        replacement_map = {"F ʟ ᴀ s ʜ": "Flash", "T E S T": "TEST"}
        
        injected = inject_prepass_into_grammar_prompt(base_prompt, replacement_map)
        
        self.assertIn(base_prompt, injected)
        self.assertIn('"F ʟ ᴀ s ʜ" → "Flash"', injected)
        self.assertIn('"T E S T" → "TEST"', injected)
        self.assertIn("PREPASS REPLACEMENTS", injected)
    
    def test_inject_prepass_into_grammar_prompt_empty_list(self):
        """Test that empty problem list returns original prompt."""
        base_prompt = "You are a grammar assistant."
        
        injected = inject_prepass_into_grammar_prompt(base_prompt, [])
        
        self.assertEqual(injected, base_prompt)
    
    def test_prepass_report_format(self):
        """Test that prepass report has expected structure."""
        expected_keys = ['source', 'created_at', 'chunks', 'summary']
        
        # Mock a typical prepass report
        mock_report = {
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
        
        # Verify all required keys are present
        for key in expected_keys:
            self.assertIn(key, mock_report)
        
        # Verify structure
        self.assertIsInstance(mock_report['chunks'], list)
        self.assertIsInstance(mock_report['summary']['unique_problem_words'], list)
    
    def test_correct_chunk_with_prepass_injection(self):
        """Test that prepass injection works in processing pipeline."""
        from backend.app import correct_chunk_with_prompt
        from prepass import DETECTOR_PROMPT
        
        # Test that our custom function exists and works
        # (This is integration-level, but important for verification)
        
        base_prompt = "Fix grammar."
        test_text = "Some text with F ʟ ᴀ s ʜ problems."
        
        # Mock the LLM call to avoid actual API call
        with patch('backend.app.call_lmstudio') as mock_call:
            mock_call.return_value = "Fixed text without problems."
            
            # Test without injection
            result1 = correct_chunk_with_prompt("http://test", "model", test_text, base_prompt)
            
            # Test with injection
            replacement_map = {"F ʟ ᴀ s ʜ": "Flash"}
            injected_prompt = inject_prepass_into_grammar_prompt(base_prompt, replacement_map)
            result2 = correct_chunk_with_prompt("http://test", "model", test_text, injected_prompt)
            
            # Both should return the mocked result
            self.assertEqual(result1, "Fixed text without problems.")
            self.assertEqual(result2, "Fixed text without problems.")
            
            # Verify that different prompts were used
            calls = mock_call.call_args_list
            self.assertEqual(len(calls), 2)
            
            # Second call should have the injected prompt
            prompt_used_1 = calls[0][0][2]  # Third argument is the prompt
            prompt_used_2 = calls[1][0][2]
            
            self.assertEqual(prompt_used_1, base_prompt)
            self.assertIn('"F ʟ ᴀ s ʜ" → "Flash"', prompt_used_2)
            self.assertIn("PREPASS REPLACEMENTS", prompt_used_2)


if __name__ == '__main__':
    unittest.main()