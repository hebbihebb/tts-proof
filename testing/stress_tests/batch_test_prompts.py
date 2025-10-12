#!/usr/bin/env python3
"""
Batch Prepass Prompt Testing

Tests multiple prompt variations quickly to find the best performing one.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from prepass_only_test import PrepassOnlyTester
from prompt_variations import PROMPT_VARIATIONS
import time
from datetime import datetime

def test_all_prompts():
    """Test all prompt variations and compare results"""
    
    results = []
    
    print("=" * 60)
    print("BATCH PREPASS PROMPT TESTING")
    print("=" * 60)
    print(f"Testing {len(PROMPT_VARIATIONS)} prompt variations...")
    print()
    
    for name, prompt in PROMPT_VARIATIONS.items():
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        
        # Create tester with custom prompt
        tester = PrepassOnlyTester(
            network_api_base="http://192.168.8.104:1234/v1",
            model="qwen3-8b"
        )
        
        # Override the prompt
        tester.prepass_prompt = prompt
        
        # Also save the prompt to a temporary file for the test
        root_dir = Path(__file__).parent.parent.parent
        prompt_file = root_dir / "prepass_prompt.txt"
        original_prompt = prompt_file.read_text(encoding='utf-8')
        
        try:
            # Write test prompt
            prompt_file.write_text(prompt, encoding='utf-8')
            
            # Run test
            start_time = time.time()
            result = tester.run_test()
            elapsed = time.time() - start_time
            
            results.append({
                'name': name,
                'accuracy': result.detection_accuracy,
                'problems_found': result.total_problems_found,
                'time': result.processing_time_seconds,
                'similarity': result.detailed_analysis['similarity_ratio'] * 100,
                'log': result.log_file
            })
            
            print(f"\n✅ {name}: {result.detection_accuracy:.1f}% accuracy, {result.total_problems_found} problems, {result.processing_time_seconds:.1f}s")
            
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            results.append({
                'name': name,
                'accuracy': 0.0,
                'problems_found': 0,
                'time': 0.0,
                'similarity': 0.0,
                'log': None,
                'error': str(e)
            })
        finally:
            # Restore original prompt
            prompt_file.write_text(original_prompt, encoding='utf-8')
    
    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print()
    
    # Sort by accuracy
    results.sort(key=lambda x: x['accuracy'], reverse=True)
    
    print(f"{'Rank':<6} {'Name':<20} {'Accuracy':<12} {'Problems':<10} {'Time':<10} {'Similarity':<12}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        if 'error' not in result:
            print(f"{i:<6} {result['name']:<20} {result['accuracy']:>8.1f}%   {result['problems_found']:>6}     {result['time']:>6.1f}s    {result['similarity']:>8.1f}%")
        else:
            print(f"{i:<6} {result['name']:<20} {'ERROR':<12} {'-':<10} {'-':<10} {'-':<12}")
    
    print()
    print(f"🏆 Best performer: {results[0]['name']} with {results[0]['accuracy']:.1f}% accuracy")
    
    # Save summary
    summary_file = Path(__file__).parent.parent / "prepass_test_results" / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    summary_file.parent.mkdir(exist_ok=True)
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("BATCH PREPASS PROMPT TESTING SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total variations tested: {len(results)}\n\n")
        
        f.write(f"{'Rank':<6} {'Name':<20} {'Accuracy':<12} {'Problems':<10} {'Time':<10} {'Similarity':<12}\n")
        f.write("-" * 80 + "\n")
        
        for i, result in enumerate(results, 1):
            if 'error' not in result:
                f.write(f"{i:<6} {result['name']:<20} {result['accuracy']:>8.1f}%   {result['problems_found']:>6}     {result['time']:>6.1f}s    {result['similarity']:>8.1f}%\n")
            else:
                f.write(f"{i:<6} {result['name']:<20} {'ERROR':<12} {'-':<10} {'-':<10} {'-':<12}\n")
                f.write(f"       Error: {result.get('error', 'Unknown')}\n")
        
        f.write(f"\n🏆 Best performer: {results[0]['name']} with {results[0]['accuracy']:.1f}% accuracy\n")
    
    print(f"\n📁 Summary saved to: {summary_file}")
    
    return results

if __name__ == "__main__":
    test_all_prompts()
