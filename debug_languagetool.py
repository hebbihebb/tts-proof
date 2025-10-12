#!/usr/bin/env python3
"""
Debug script to see what LanguageTool detects and how our category mapping handles it.
"""
import logging
from mdp.grammar_assist import apply_grammar_corrections, _map_languagetool_category
from mdp.config import load_config
from mdp.markdown_adapter import mask_protected, unmask

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def debug_grammar_check(input_file: str):
    """Run grammar check with detailed logging."""
    # Load config
    config = load_config()
    
    # Read input
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Apply Phase 1 masking
    masked_text, mask_table = mask_protected(text)
    
    # Initialize LanguageTool
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool('en')
    except Exception as e:
        logger.error(f"Failed to initialize LanguageTool: {e}")
        return
    
    # Get ALL matches (before filtering)
    matches = tool.check(masked_text)
    
    print(f"\n{'='*80}")
    print(f"LanguageTool found {len(matches)} potential issues")
    print(f"{'='*80}\n")
    
    safe_categories = config.get('grammar_assist', {}).get('safe_categories', [])
    print(f"Our safe categories: {safe_categories}\n")
    
    accepted = 0
    rejected = 0
    
    for i, match in enumerate(matches, 1):
        # Get our mapped category
        our_category = _map_languagetool_category(match.ruleId, match.category)
        is_safe = our_category in safe_categories if our_category else False
        
        print(f"Issue #{i}: {'✅ ACCEPTED' if is_safe else '❌ REJECTED'}")
        print(f"  Rule ID: {match.ruleId}")
        print(f"  LT Category: {match.category}")
        print(f"  Our Category: {our_category if our_category else 'None (unmapped)'}")
        print(f"  Message: {match.message}")
        print(f"  Context: {match.context}")
        if match.replacements:
            print(f"  Suggested: {match.replacements[:3]}")
        print()
        
        if is_safe:
            accepted += 1
        else:
            rejected += 1
    
    print(f"{'='*80}")
    print(f"Summary: {accepted} accepted, {rejected} rejected")
    print(f"{'='*80}\n")
    
    tool.close()
    
    # Now run the actual grammar assist to compare
    print("Running actual grammar assist...\n")
    corrected, stats = apply_grammar_corrections(masked_text, config, mask_table)
    print(f"Stats from apply_grammar_corrections: {stats}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python debug_languagetool.py <input.md>")
        sys.exit(1)
    
    debug_grammar_check(sys.argv[1])
