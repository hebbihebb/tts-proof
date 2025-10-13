"""
Phase 8 - Fixer: Light polish on text nodes using bigger model

This module provides careful, minimal polish on already-sanitized text nodes.
Uses a larger model (e.g., Qwen2.5-1.5B-Instruct) with strict safety guardrails.

Key safety features:
- Operates only on text nodes (never sees Markdown)
- Rejects outputs with markdown tokens
- Enforces length limits (20% per node, 5% per file)
- Fails safe to original text on any rejection
- Reuses Phase 7 structural validators
"""

from .fixer import apply_fixer

__all__ = ['apply_fixer']
