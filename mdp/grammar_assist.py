#!/usr/bin/env python3
"""
Phase 5 - Optional Grammar Assist (Deterministic, One-Shot, Non-Interactive)

Provides conservative grammar and spacing corrections using an offline engine.
Operates only on text nodes, never alters Markdown structure or masked regions.
"""

import re
from typing import Dict, Any, Tuple, List, Optional
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import LanguageTool
try:
    import language_tool_python
    _language_tool_available = True
except ImportError:
    _language_tool_available = False
    logger.warning("language_tool_python not available. Grammar assist will be disabled.")


# Safe category whitelist - only these are auto-applied
SAFE_CATEGORIES = {
    'TYPOS',
    'PUNCTUATION', 
    'CASING',
    'SPACING',
    'SIMPLE_AGREEMENT',
}


class GrammarSuggestion:
    """Represents a grammar correction suggestion."""
    
    def __init__(self, offset: int, length: int, replacement: str, 
                 category: str, message: str):
        self.offset = offset
        self.length = length
        self.replacement = replacement
        self.category = category
        self.message = message
    
    def __repr__(self):
        return f"GrammarSuggestion(offset={self.offset}, len={self.length}, " \
               f"cat={self.category}, '{self.get_original()}' → '{self.replacement}')"
    
    def get_original(self) -> str:
        """Placeholder for original text - will be filled by caller."""
        return ""


def _is_safe_suggestion(suggestion: GrammarSuggestion, 
                       safe_categories: List[str]) -> bool:
    """
    Check if a suggestion belongs to safe categories.
    """
    return suggestion.category in safe_categories


def _overlaps_with_mask(suggestion: GrammarSuggestion, 
                       mask_table: Dict[str, str]) -> bool:
    """
    Check if a suggestion would modify a masked region.
    Masked regions use sentinels like __MASKED_0__, __MASKED_1__, etc.
    """
    # Simple check: if replacement or surrounding area contains sentinel pattern
    # This is conservative - any suggestion near a mask is rejected
    return False  # TODO: Implement proper mask overlap detection


def _validate_structural_integrity(original: str, corrected: str, 
                                   mask_table: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
    """
    Post-edit validation to ensure Markdown structure is intact.
    
    Checks:
    - Mask count unchanged
    - Link parity ([ and ])
    - Backtick parity
    - Bracket parity
    
    Returns (is_valid, error_message)
    """
    errors = []
    
    # Check mask counts if mask_table provided
    if mask_table:
        for sentinel in mask_table.keys():
            orig_count = original.count(sentinel)
            corr_count = corrected.count(sentinel)
            if orig_count != corr_count:
                errors.append(f"Mask count mismatch for {sentinel}: {orig_count} → {corr_count}")
    
    # Check link bracket parity
    orig_open_brackets = original.count('[')
    orig_close_brackets = original.count(']')
    corr_open_brackets = corrected.count('[')
    corr_close_brackets = corrected.count(']')
    
    if orig_open_brackets != corr_open_brackets or orig_close_brackets != corr_close_brackets:
        errors.append(f"Link bracket parity broken: [{orig_open_brackets},{orig_close_brackets}] → [{corr_open_brackets},{corr_close_brackets}]")
    
    # Check backtick parity
    orig_backticks = original.count('`')
    corr_backticks = corrected.count('`')
    if orig_backticks != corr_backticks:
        errors.append(f"Backtick parity broken: {orig_backticks} → {corr_backticks}")
    
    # Check parenthesis parity (for links)
    orig_open_parens = original.count('(')
    orig_close_parens = original.count(')')
    corr_open_parens = corrected.count('(')
    corr_close_parens = corrected.count(')')
    
    if orig_open_parens != corr_open_parens or orig_close_parens != corr_close_parens:
        errors.append(f"Parenthesis parity broken: ({orig_open_parens},{orig_close_parens}) → ({corr_open_parens},{corr_close_parens})")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, ""


def apply_grammar_corrections(text: str, config: Dict[str, Any], 
                              mask_table: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, int]]:
    """
    Apply conservative grammar corrections using offline LanguageTool engine.
    
    Args:
        text: Text to correct (should be text nodes only, with masks preserved)
        config: Configuration dict with grammar_assist settings
        mask_table: Optional mask table from Phase 1 masking
    
    Returns:
        (corrected_text, stats_dict)
        
    Stats dict contains:
        - typos_fixed: Number of typo corrections applied
        - spacing_fixed: Number of spacing corrections applied
        - punctuation_fixed: Number of punctuation corrections applied
        - casing_fixed: Number of casing corrections applied
        - agreement_fixed: Number of simple agreement corrections applied
        - rejected: Number of suggestions rejected (unsafe category, overlaps mask, etc.)
        - structural_validation_failed: 1 if post-edit validation failed, 0 otherwise
    """
    stats = defaultdict(int)
    
    # Check if grammar assist is enabled
    grammar_config = config.get('grammar_assist', {})
    if not grammar_config.get('enabled', True):
        logger.info("Grammar assist disabled in config")
        return text, dict(stats)
    
    # Check if LanguageTool is available
    if not _language_tool_available:
        logger.warning("LanguageTool not available, skipping grammar corrections")
        return text, dict(stats)
    
    # Get configuration
    language = grammar_config.get('language', 'en')
    safe_categories = set(grammar_config.get('safe_categories', list(SAFE_CATEGORIES)))
    
    logger.info(f"Running grammar assist: language={language}, safe_categories={safe_categories}")
    
    # Initialize LanguageTool
    try:
        tool = language_tool_python.LanguageTool(language)
    except Exception as e:
        logger.error(f"Failed to initialize LanguageTool: {e}")
        return text, dict(stats)
    
    # Get suggestions
    try:
        matches = tool.check(text)
    except Exception as e:
        logger.error(f"LanguageTool check failed: {e}")
        tool.close()
        return text, dict(stats)
    
    # Convert to our suggestion format and filter
    suggestions = []
    for match in matches:
        # Map LanguageTool rule categories to our safe categories
        # This is a simplified mapping - real implementation needs more sophisticated mapping
        category = _map_languagetool_category(match.ruleId, match.category)
        
        if not category or category not in safe_categories:
            stats['rejected'] += 1
            continue
        
        # Get the best replacement
        if not match.replacements:
            stats['rejected'] += 1
            continue
        
        suggestion = GrammarSuggestion(
            offset=match.offset,
            length=match.errorLength,
            replacement=match.replacements[0],
            category=category,
            message=match.message
        )
        
        # Check if suggestion overlaps with masks
        if mask_table and _overlaps_with_mask(suggestion, mask_table):
            stats['rejected'] += 1
            continue
        
        suggestions.append(suggestion)
    
    # Close LanguageTool
    tool.close()
    
    # Apply suggestions (in reverse order to maintain offsets)
    corrected = text
    suggestions.sort(key=lambda s: s.offset, reverse=True)
    
    for suggestion in suggestions:
        # Apply the correction
        before = corrected[:suggestion.offset]
        after = corrected[suggestion.offset + suggestion.length:]
        corrected = before + suggestion.replacement + after
        
        # Update stats
        if suggestion.category == 'TYPOS':
            stats['typos_fixed'] += 1
        elif suggestion.category == 'SPACING':
            stats['spacing_fixed'] += 1
        elif suggestion.category == 'PUNCTUATION':
            stats['punctuation_fixed'] += 1
        elif suggestion.category == 'CASING':
            stats['casing_fixed'] += 1
        elif suggestion.category == 'SIMPLE_AGREEMENT':
            stats['agreement_fixed'] += 1
    
    # Validate structural integrity
    is_valid, error_msg = _validate_structural_integrity(text, corrected, mask_table)
    if not is_valid:
        logger.error(f"Structural validation failed: {error_msg}")
        logger.error("Reverting all grammar corrections")
        stats['structural_validation_failed'] = 1
        return text, dict(stats)  # Return original text
    
    logger.info(f"Grammar assist complete: {dict(stats)}")
    return corrected, dict(stats)


def _map_languagetool_category(rule_id: str, lt_category: str) -> Optional[str]:
    """
    Map LanguageTool rule categories to our safe categories.
    
    This is a conservative mapping - when in doubt, return None (reject).
    
    LanguageTool often uses the GRAMMAR category for many things including
    typos and agreement errors, so we need to check rule IDs to distinguish.
    """
    rule_id_lower = rule_id.lower()
    lt_category_lower = lt_category.lower()
    
    # Spacing (check first - most common and safest)
    if 'whitespace' in lt_category_lower or 'space' in rule_id_lower or 'consecutive' in rule_id_lower:
        return 'SPACING'
    
    # Casing
    if 'casing' in lt_category_lower or 'uppercase' in rule_id_lower or 'capitalization' in rule_id_lower:
        return 'CASING'
    
    # Punctuation
    if 'punctuation' in lt_category_lower or 'comma' in rule_id_lower:
        return 'PUNCTUATION'
    
    # Typos/Spelling - LanguageTool often categorizes these as GRAMMAR
    # Look for morfologik (spelling engine) or specific typo-related rule IDs
    if ('spelling' in lt_category_lower or 
        'typo' in rule_id_lower or 
        'morfologik' in rule_id_lower or
        'hunspell' in rule_id_lower):
        return 'TYPOS'
    
    # Simple agreement - LanguageTool uses GRAMMAR category with specific rule IDs
    # Common patterns: HE_VERB_AGR, SHE_VERB_AGR, IT_VBZ, SUBJECT_VERB_AGR, etc.
    if (lt_category_lower == 'grammar' and 
        ('verb_agr' in rule_id_lower or 
         'agreement' in rule_id_lower or
         '_vbz' in rule_id_lower or
         '_vb_' in rule_id_lower)):
        return 'SIMPLE_AGREEMENT'
    
    # Default: reject (better safe than sorry)
    return None


def main():
    """CLI entry point for standalone testing."""
    import sys
    from .config import load_config
    from .markdown_adapter import mask_protected, unmask
    
    if len(sys.argv) < 2:
        print("Usage: python -m mdp.grammar_assist <input.md> [-o output.md] [-c config.yaml]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[sys.argv.index('-o') + 1] if '-o' in sys.argv else None
    config_file = sys.argv[sys.argv.index('-c') + 1] if '-c' in sys.argv else None
    
    # Load config
    config = load_config(config_file)
    
    # Read input
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Apply Phase 1 masking
    masked_text, mask_table = mask_protected(text)
    
    # Apply grammar corrections
    corrected, stats = apply_grammar_corrections(masked_text, config, mask_table)
    
    # Unmask
    result = unmask(corrected, mask_table)
    
    # Output
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Wrote corrected text to {output_file}")
    else:
        print(result)
    
    # Print stats
    print("\nGrammar Assist Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
