"""
Unit tests for fixer/client.py

Tests LM Studio client with timeout, retry, and error handling.
All tests use mocks - no real API calls.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from fixer.client import FixerClient, call_fixer_model


class TestFixerClient:
    """Test FixerClient class."""
    
    def test_successful_call(self):
        """Successful API call returns response text."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Fixed text here'}}
            ]
        }
        
        with patch('requests.post', return_value=mock_response):
            client = FixerClient(config)
            result, error = client.call_model("system prompt", "user prompt")
            
            assert result == "Fixed text here"
            assert error == ""
    
    def test_timeout_returns_error(self):
        """Timeout should return error message, not raise."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        with patch('requests.post', side_effect=requests.Timeout()):
            client = FixerClient(config)
            result, error = client.call_model("system prompt", "user prompt")
            
            assert result == ""
            assert "Timeout" in error
    
    def test_connection_error_raises_connection_error(self):
        """Connection error should raise ConnectionError."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        with patch('requests.post', side_effect=requests.ConnectionError()):
            client = FixerClient(config)
            with pytest.raises(ConnectionError, match="unreachable"):
                client.call_model("system prompt", "user prompt")
    
    def test_retries_on_failure(self):
        """Client should retry on failure."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 2,  # 2 retries = 3 attempts total
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        # First two attempts fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Success on retry'}}
            ]
        }
        
        with patch('requests.post', side_effect=[
            requests.Timeout(),
            requests.Timeout(),
            mock_response
        ]):
            client = FixerClient(config)
            result, error = client.call_model("system prompt", "user prompt")
            
            assert result == "Success on retry"
            assert error == ""
    
    def test_max_retries_exhausted(self):
        """Should return error after exhausting retries."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 2,  # 2 retries = 3 attempts total
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        with patch('requests.post', side_effect=requests.Timeout()):
            client = FixerClient(config)
            result, error = client.call_model("system prompt", "user prompt")
            
            assert result == ""
            assert "Timeout" in error
    
    def test_http_error_returns_error_message(self):
        """HTTP errors should return error message, not raise."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('requests.post', return_value=mock_response):
            client = FixerClient(config)
            result, error = client.call_model("system prompt", "user prompt")
            
            assert result == ""
            assert "500" in error
    
    def test_malformed_json_returns_error(self):
        """Malformed JSON response should return error message."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'no_choices': 'malformed'}
        
        with patch('requests.post', return_value=mock_response):
            client = FixerClient(config)
            result, error = client.call_model("system prompt", "user prompt")
            
            assert result == ""
            assert "Empty response" in error
    
    def test_seed_included_in_request(self):
        """Seed should be included in API request for determinism."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 42
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Fixed text'}}
            ]
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            client = FixerClient(config)
            client.call_model("system prompt", "user prompt")
            
            # Check that seed was included in the request
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['seed'] == 42
    
    def test_token_limits_included_in_request(self):
        """Token limits should be included in API request."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 2048,
            'max_output_tokens': 512,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.3,
            'top_p': 0.8,
            'seed': 7
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Fixed text'}}
            ]
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            client = FixerClient(config)
            client.call_model("system prompt", "user prompt")
            
            # Check token limits and sampling params
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['max_tokens'] == 512
            assert payload['temperature'] == 0.3
            assert payload['top_p'] == 0.8


class TestCallFixerModel:
    """Test convenience function call_fixer_model."""
    
    def test_convenience_function_works(self):
        """call_fixer_model should work as shortcut."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [
                {'message': {'content': 'Fixed text'}}
            ]
        }
        
        with patch('requests.post', return_value=mock_response):
            result = call_fixer_model(
                'http://test:1234/v1',
                'test-model',
                "system prompt",
                "user text",
                config
            )
            
            assert result == "Fixed text"
    
    def test_convenience_function_propagates_connection_error(self):
        """call_fixer_model should propagate ConnectionError."""
        config = {
            'api_base': 'http://test:1234/v1',
            'model': 'test-model',
            'max_context_tokens': 1024,
            'max_output_tokens': 256,
            'timeout_s': 10,
            'retries': 1,
            'temperature': 0.2,
            'top_p': 0.9,
            'seed': 7
        }
        
        with patch('requests.post', side_effect=requests.ConnectionError()):
            with pytest.raises(ConnectionError):
                call_fixer_model(
                    'http://test:1234/v1',
                    'test-model',
                    "system prompt",
                    "user text",
                    config
                )
