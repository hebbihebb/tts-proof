#!/usr/bin/env python3
"""
fixer/prompt.py - Prompt Templates for Fixer

Conservative line-editor instructions with minimal few-shot examples.
"""

from typing import Dict, Any


def build_system_prompt(locale: str = "en") -> str:
    """
    Build system prompt for fixer model.
    
    Args:
        locale: Language code (e.g., "en", "is")
    
    Returns:
        System prompt string
    """
    base_instructions = """You are a careful line editor for prose. Improve clarity and grammar without changing meaning, tone, or details. Do not add or remove facts, names, or events. Output the revised TEXT only. No explanations, no lists, no quotes, no markdown, no code, no JSON—just plain text."""
    
    # Optional: Add tiny few-shot examples (< 40 tokens total)
    # For now, keeping it instruction-only for maximum conservation
    few_shot = """

Examples:
Before: "The cat it sat on the mat and, it was comfortable."
After: "The cat sat on the mat and was comfortable."

Before: "She walk to the store yesterday."
After: "She walked to the store yesterday."
"""
    
    # Decide whether to include few-shot (can be toggled based on testing)
    use_few_shot = False  # Conservative: instructions only
    
    if use_few_shot:
        return f"{base_instructions}\n\nLanguage: {locale}{few_shot}"
    else:
        return f"{base_instructions}\n\nLanguage: {locale}"


def build_user_prompt(text: str) -> str:
    """
    Build user prompt wrapping text to fix.
    
    Args:
        text: Text span to improve
    
    Returns:
        User prompt string with delimiters
    """
    return f"""TEXT:
<<<
{text}
>>>
Return only the improved text for TEXT. No additional content."""


def get_prompts(text: str, config: Dict[str, Any]) -> tuple[str, str]:
    """
    Generate system and user prompts from config and text.
    
    Args:
        text: Text to fix
        config: Fixer configuration
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    locale = config.get('locale', 'en')
    system_prompt = build_system_prompt(locale)
    user_prompt = build_user_prompt(text)
    return system_prompt, user_prompt
