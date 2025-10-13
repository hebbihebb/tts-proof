#!/usr/bin/env python3
"""
fixer/client.py - Fixer Model Client Wrapper

Handles communication with local LLM for text polishing.
Simpler than detector client - returns plain text, no JSON parsing.
"""

import logging
from typing import Dict, Any, Tuple
import requests

logger = logging.getLogger(__name__)


class FixerClient:
    """Wrapper for fixer model API calls with safety guardrails."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize client with configuration.
        
        Args:
            config: Fixer configuration dict
        """
        self.api_base = config.get('api_base', 'http://127.0.0.1:1234/v1')
        self.model = config.get('model', 'qwen2.5-1.5b-instruct')
        self.max_context_tokens = config.get('max_context_tokens', 1024)
        self.max_output_tokens = config.get('max_output_tokens', 256)
        self.timeout_s = config.get('timeout_s', 10)
        self.retries = config.get('retries', 1)
        self.temperature = config.get('temperature', 0.2)
        self.top_p = config.get('top_p', 0.9)
        self.seed = config.get('seed', 7)  # For determinism
    
    def call_model(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """
        Call the model with prompts.
        
        Args:
            system_prompt: System message
            user_prompt: User message (contains text to fix)
        
        Returns:
            Tuple of (response_text, error_message)
            If successful, error_message is empty.
            If failed, response_text is empty and error_message explains why.
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
            "max_tokens": self.max_output_tokens,
            "stream": False
        }
        
        # Add seed if supported by backend
        if self.seed is not None:
            payload["seed"] = self.seed
        
        for attempt in range(self.retries + 1):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    json=payload,
                    timeout=self.timeout_s
                )
                
                if response.status_code != 200:
                    error_msg = f"API returned status {response.status_code}"
                    logger.warning(f"Fixer model call failed (attempt {attempt + 1}): {error_msg}")
                    if attempt < self.retries:
                        continue
                    return "", error_msg
                
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                if not content:
                    error_msg = "Empty response from model"
                    logger.warning(f"Fixer model call failed (attempt {attempt + 1}): {error_msg}")
                    if attempt < self.retries:
                        continue
                    return "", error_msg
                
                # Return plain text response
                return content.strip(), ""
            
            except requests.Timeout:
                error_msg = f"Timeout after {self.timeout_s}s"
                logger.warning(f"Fixer model call failed (attempt {attempt + 1}): {error_msg}")
                if attempt < self.retries:
                    continue
                return "", error_msg
            
            except requests.ConnectionError as e:
                error_msg = f"Connection error: {str(e)}"
                logger.warning(f"Fixer model call failed (attempt {attempt + 1}): {error_msg}")
                if attempt < self.retries:
                    continue
                # On last retry, raise ConnectionError for exit code 2
                if attempt == self.retries:
                    raise ConnectionError(f"Fixer model server unreachable: {error_msg}")
                return "", error_msg
            
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                logger.warning(f"Fixer model call failed (attempt {attempt + 1}): {error_msg}")
                if attempt < self.retries:
                    continue
                return "", error_msg
        
        return "", "All retries exhausted"


def call_fixer_model(
    api_base: str,
    model: str,
    system_prompt: str,
    user_text: str,
    config: Dict[str, Any]
) -> str:
    """
    Convenience function to call fixer model.
    
    Args:
        api_base: API base URL
        model: Model name
        system_prompt: System instructions
        user_text: Text to fix
        config: Full fixer configuration
    
    Returns:
        Fixed text (empty string on error)
    
    Raises:
        ConnectionError: If model server is unreachable after retries
    """
    client = FixerClient(config)
    response, error = client.call_model(system_prompt, user_text)
    
    if error:
        logger.error(f"Fixer model call failed: {error}")
        # ConnectionError already raised by client if applicable
        return ""
    
    return response
