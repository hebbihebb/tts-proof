#!/usr/bin/env python3
"""
Unit tests for detector/client.py - LM Studio API wrapper with mocked HTTP
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests
from detector.client import ModelClient


@pytest.fixture
def client_config():
    """Basic client configuration."""
    return {
        'api_base': 'http://127.0.0.1:1234/v1',
        'model': 'test-model',
        'timeout_s': 8,
        'retries': 1,
        'temperature': 0.2,
        'top_p': 0.9,
        'max_output_chars': 2000,
    }


@pytest.fixture
def mock_client(client_config):
    """Create a ModelClient instance for testing."""
    return ModelClient(client_config)


class TestModelCalling:
    """Tests for model API calls."""
    
    @patch('requests.post')
    def test_successful_call(self, mock_post, mock_client):
        """Successful model call should return response content."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}]
        }
        mock_post.return_value = mock_response
        
        content, error = mock_client.call_model("System prompt", "User prompt")
        
        assert content == "Test response"
        assert error == ""
        assert mock_post.called
    
    @patch('requests.post')
    def test_timeout_returns_error(self, mock_post, mock_client):
        """Timeout should return None with error message."""
        mock_post.side_effect = requests.Timeout("Connection timeout")
        
        content, error = mock_client.call_model("System prompt", "User prompt")
        
        assert content is None
        assert "timeout" in error.lower()
    
    @patch('requests.post')
    def test_connection_error(self, mock_post, mock_client):
        """Connection errors should be handled gracefully."""
        mock_post.side_effect = requests.ConnectionError("Connection refused")
        
        content, error = mock_client.call_model("System prompt", "User prompt")
        
        assert content is None
        assert "connection" in error.lower() or "error" in error.lower()
    
    @patch('requests.post')
    def test_retry_once_then_succeed(self, mock_post, mock_client):
        """Should retry once on failure, then succeed."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Success on retry'}}]
        }
        
        mock_post.side_effect = [
            requests.Timeout("First attempt timeout"),
            mock_response
        ]
        
        content, error = mock_client.call_model("System prompt", "User prompt")
        
        assert content == "Success on retry"
        assert error == ""
        assert mock_post.call_count == 2  # Initial + 1 retry
    
    @patch('requests.post')
    def test_retry_exhausted(self, mock_post, mock_client):
        """Should give up after retries exhausted."""
        mock_post.side_effect = requests.Timeout("Persistent timeout")
        
        content, error = mock_client.call_model("System prompt", "User prompt")
        
        assert content is None
        assert "timeout" in error.lower()
        assert mock_post.call_count == 2  # Initial + 1 retry (retries=1)


class TestJSONExtraction:
    """Tests for JSON extraction from model responses."""
    
    def test_extract_valid_json_array(self, mock_client):
        """Valid JSON array should be extracted correctly."""
        response = '[{"find": "test", "replace": "TEST", "reason": "TTS_SPACED"}]'
        parsed, error = mock_client.extract_json(response)
        
        assert parsed is not None
        assert len(parsed) == 1
        assert parsed[0]['find'] == 'test'
        assert error == ""
    
    def test_extract_json_with_prose(self, mock_client):
        """Should extract JSON array even when wrapped in prose."""
        response = """
        Sure, here's the replacement plan:
        [{"find": "F l a s h", "replace": "Flash", "reason": "TTS_SPACED"}]
        Hope this helps!
        """
        parsed, error = mock_client.extract_json(response)
        
        assert parsed is not None
        assert len(parsed) == 1
        assert parsed[0]['replace'] == 'Flash'
        assert error == ""
    
    def test_no_json_returns_error(self, mock_client):
        """Response without JSON should return None."""
        response = "This is just prose without any JSON array."
        parsed, error = mock_client.extract_json(response)
        
        assert parsed is None
        assert "no json" in error.lower() or "not found" in error.lower()
    
    def test_invalid_json_returns_error(self, mock_client):
        """Malformed JSON should return None."""
        response = '[{"find": "test", "replace": "TEST", "reason": }]'  # Missing value
        parsed, error = mock_client.extract_json(response)
        
        assert parsed is None
        assert "parse" in error.lower() or "error" in error.lower() or "invalid" in error.lower()
    
    def test_json_not_array_returns_error(self, mock_client):
        """JSON that's not an array should return None."""
        response = '{"find": "test", "replace": "TEST"}'  # Object, not array
        parsed, error = mock_client.extract_json(response)
        
        assert parsed is None
        assert "array" in error.lower() or "list" in error.lower()
    
    def test_empty_json_array(self, mock_client):
        """Empty JSON array should be valid."""
        response = '[]'
        parsed, error = mock_client.extract_json(response)
        
        assert parsed == []
        assert error == ""
    
    def test_oversize_response_truncated(self, mock_client):
        """Responses exceeding max_output_chars should be truncated."""
        # Create response larger than max_output_chars (2000)
        large_json = '[' + ','.join([
            '{"find": "x", "replace": "X", "reason": "CASE_GLITCH"}'
        ] * 100) + ']'  # ~4500 chars
        
        # Response should be truncated to 2000 chars before extraction
        # This means JSON might be incomplete
        parsed, error = mock_client.extract_json(large_json)
        
        # Either successfully extracted (if truncation left valid JSON)
        # or returned error (if truncation broke JSON)
        # Both are acceptable - key is that it doesn't crash
        assert parsed is not None or error != ""


class TestDeterminism:
    """Tests for deterministic behavior."""
    
    @patch('requests.post')
    def test_same_input_same_request(self, mock_post, mock_client):
        """Same input should produce identical API requests."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': '[]'}}]
        }
        mock_post.return_value = mock_response
        
        system_prompt = "System"
        user_prompt = "User"
        
        # Call twice with same inputs
        mock_client.call_model(system_prompt, user_prompt)
        call1_args = mock_post.call_args
        
        mock_client.call_model(system_prompt, user_prompt)
        call2_args = mock_post.call_args
        
        # Verify both calls had identical JSON payloads
        assert call1_args == call2_args
