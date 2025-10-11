#!/usr/bin/env python3
"""
Integration test to demonstrate prepass + grammar correction.
"""

import json
from pathlib import Path
from prepass import load_prepass_report, get_problem_words_for_grammar, inject_prepass_into_grammar_prompt

def test_prepass_grammar_integration():
    """Test the complete prepass + grammar integration."""
    
    print("=== TTS-Proof Prepass Integration Test ===\n")
    
    # Load the prepass report we just created
    report_path = Path("test_prepass_custom.json")
    if not report_path.exists():
        print(f"Error: {report_path} not found. Run prepass first.")
        return
    
    print(f"Loading prepass report: {report_path}")
    report = load_prepass_report(report_path)
    
    print(f"Report summary:")
    print(f"  Source: {report['source']}")
    print(f"  Unique problems: {len(report['summary']['unique_problem_words'])}")
    print(f"  Chunks: {len(report['chunks'])}")
    print()
    
    # Get problem words for grammar injection
    problem_words = get_problem_words_for_grammar(report)
    print(f"Problem words for grammar injection:")
    for i, word in enumerate(problem_words):
        print(f"  {i+1}. '{word}'")
    print()
    
    # Test grammar prompt injection
    base_prompt = """You are a Markdown-preserving cleaner for TTS.
Rules: Fix grammar, spelling, and normalize weird text patterns.
Keep all Markdown structure intact."""
    
    print("Original grammar prompt:")
    print(f"  {base_prompt}")
    print()
    
    # Inject prepass words
    injected_prompt = inject_prepass_into_grammar_prompt(base_prompt, problem_words)
    
    print("Grammar prompt with prepass injection:")
    print(f"  {injected_prompt}")
    print()
    
    # Show what the injection adds
    injection_part = injected_prompt[len(base_prompt):].strip()
    print("Injection added:")
    print(f"  {injection_part}")
    print()
    
    print("✓ Integration test complete!")
    print()
    print("To test full processing with prepass:")
    print("1. Use the web UI with the 'Use prepass in grammar correction' toggle")
    print("2. Or implement CLI flag in md_proof.py to load and use prepass report")

if __name__ == '__main__':
    test_prepass_grammar_integration()