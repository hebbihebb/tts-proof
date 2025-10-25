#!/usr/bin/env python3
"""
Test Two-Pass Workflow: Detect → Grammar
Compare with current Detect → Apply approach
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from md_processor import run_pipeline, get_default_config


def test_two_pass():
    """Test the two-pass detect → grammar workflow."""
    test_dir = Path(__file__).parent / "test_data"
    results_dir = Path(__file__).parent / "stress_test_results"
    
    with open(test_dir / "tts_stress_test.md", 'r', encoding='utf-8') as f:
        test_input = f.read()
    
    config = get_default_config()
    config['detector']['chunk_size'] = 8000  # Historical chunk size
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("="*60)
    print("TWO-PASS WORKFLOW TEST")
    print("="*60)
    
    # Test 1: Current approach (detect → apply)
    print("\n📊 Test 1: Current (detect → apply)")
    print("-" * 60)
    try:
        steps1 = ['mask', 'prepass-basic', 'prepass-advanced', 'detect', 'apply']
        result1, stats1 = run_pipeline(
            test_input,
            steps=steps1,
            config=config,
            llm_endpoint='http://localhost:1234/v1',
            llm_model='qwen3-8b'
        )
        
        output1 = results_dir / f"two_pass_detect_apply_{timestamp}.md"
        with open(output1, 'w', encoding='utf-8') as f:
            f.write(result1)
        
        print(f"✅ Saved to: {output1.name}")
        print(f"Stats: {json.dumps(stats1, indent=2)}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        result1 = None
        stats1 = None
    
    # Test 2: Two-pass approach (detect → grammar)
    print("\n📊 Test 2: Two-Pass (detect → grammar)")
    print("-" * 60)
    try:
        steps2 = ['mask', 'prepass-basic', 'prepass-advanced', 'detect', 'grammar']
        result2, stats2 = run_pipeline(
            test_input,
            steps=steps2,
            config=config,
            llm_endpoint='http://localhost:1234/v1',
            llm_model='qwen3-8b'
        )
        
        output2 = results_dir / f"two_pass_detect_grammar_{timestamp}.md"
        with open(output2, 'w', encoding='utf-8') as f:
            f.write(result2)
        
        print(f"✅ Saved to: {output2.name}")
        print(f"Stats: {json.dumps(stats2, indent=2)}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        result2 = None
        stats2 = None
    
    # Test 3: Three-pass approach (detect → apply → grammar)
    print("\n📊 Test 3: Three-Pass (detect → apply → grammar)")
    print("-" * 60)
    try:
        steps3 = ['mask', 'prepass-basic', 'prepass-advanced', 'detect', 'apply', 'grammar']
        result3, stats3 = run_pipeline(
            test_input,
            steps=steps3,
            config=config,
            llm_endpoint='http://localhost:1234/v1',
            llm_model='qwen3-8b'
        )
        
        output3 = results_dir / f"two_pass_detect_apply_grammar_{timestamp}.md"
        with open(output3, 'w', encoding='utf-8') as f:
            f.write(result3)
        
        print(f"✅ Saved to: {output3.name}")
        print(f"Stats: {json.dumps(stats3, indent=2)}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        result3 = None
        stats3 = None
    
    # Calculate similarities
    print("\n" + "="*60)
    print("COMPARISON WITH REFERENCE")
    print("="*60)
    
    with open(test_dir / "tts_stress_test_reference.md", 'r', encoding='utf-8') as f:
        reference = f.read()
    
    import difflib
    
    if result1:
        sim1 = difflib.SequenceMatcher(None, result1, reference).ratio()
        print(f"\n1. detect → apply: {sim1:.2%}")
    
    if result2:
        sim2 = difflib.SequenceMatcher(None, result2, reference).ratio()
        print(f"2. detect → grammar: {sim2:.2%}")
    
    if result3:
        sim3 = difflib.SequenceMatcher(None, result3, reference).ratio()
        print(f"3. detect → apply → grammar: {sim3:.2%}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_two_pass()
