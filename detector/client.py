#!/usr/bin/env python3
"""
detector/client.py - Model Client Wrapper

Handles communication with local LLM with timeouts, retries, and JSON extraction.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class ModelClient:
    """Wrapper for local model API calls with safety guardrails."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize client with configuration.
        
        Args:
            config: Detector configuration dict
        """
        self.api_base = config.get('api_base', 'http://127.0.0.1:1234/v1')
        self.model = config.get('model', 'qwen-1_8b-instruct')
        self.max_context_tokens = config.get('max_context_tokens', 1024)
        self.timeout_s = config.get('timeout_s', 8)
        self.retries = config.get('retries', 1)
        self.temperature = config.get('temperature', 0.2)
        self.top_p = config.get('top_p', 0.9)
        self.max_output_chars = config.get('max_output_chars', 2000)
    
    def call_model(self, system_prompt: str, user_prompt: str) -> Tuple[Optional[str], str]:
        """
        Call the model with prompts.
        
        Args:
            system_prompt: System message
            user_prompt: User message
        
        Returns:
            Tuple of (response_text, error_message)
            If successful, error_message is empty.
            If failed, response_text is None and error_message explains why.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_context_tokens,
            "stream": False
        }
        
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    timeout=self.timeout_s
                )
                
                if response.status_code != 200:
                    error_msg = f"API returned status {response.status_code}"
                    logger.warning(f"Model call failed (attempt {attempt + 1}): {error_msg}")
                    if attempt < self.retries:
                        continue
                    return None, error_msg
                
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                if not content:
                    error_msg = "Empty response from model"
                    logger.warning(f"Model call failed (attempt {attempt + 1}): {error_msg}")
                    if attempt < self.retries:
                        continue
                    return None, error_msg
                
                # Truncate if too long
                if len(content) > self.max_output_chars:
                    logger.warning(f"Response truncated from {len(content)} to {self.max_output_chars} chars")
                    content = content[:self.max_output_chars]
                
                return content, ""
            
            except requests.Timeout:
                error_msg = f"Timeout after {self.timeout_s}s"
                logger.warning(f"Model call failed (attempt {attempt + 1}): {error_msg}")
                if attempt < self.retries:
                    continue
                return None, error_msg
            
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                logger.warning(f"Model call failed (attempt {attempt + 1}): {error_msg}")
                if attempt < self.retries:
                    continue
                return None, error_msg
        
        return None, "All retries exhausted"
    
    def extract_json(self, response: str) -> Tuple[Optional[list], str]:
        """
        Extract JSON array from model response.
        
        Args:
            response: Raw model response
        
        Returns:
            Tuple of (parsed_json, error_message)
        """
        if not response:
            return None, "Empty response"
        
        # Try to find JSON array in response (model might add prose)
        # Look for [ ... ] pattern
        json_pattern = r'\[.*?\]'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if not matches:
            # Try parsing entire response as JSON
            try:
                parsed = json.loads(response)
                if isinstance(parsed, list):
                    return parsed, ""
                return None, "Response is not a JSON array"
            except json.JSONDecodeError as e:
                return None, f"No JSON array found: {str(e)}"
        
        # Try each match (usually just one)
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, list):
                    return parsed, ""
            except json.JSONDecodeError:
                continue
        
        return None, "Could not parse any JSON array from response"
