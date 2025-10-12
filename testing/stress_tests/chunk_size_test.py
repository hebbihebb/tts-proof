#!/usr/bin/env python3
"""
Quick chunk size comparison test
"""

from stress_test_system import StressTestSystem

def test_chunk_sizes():
    """Test different chunk sizes to see quality impact"""
    
    chunk_sizes = [2000, 4000, 8000]
    results = []
    
    for chunk_size in chunk_sizes:
        print(f"\n=== TESTING CHUNK SIZE: {chunk_size} ===")
        
        tester = StressTestSystem()
        
        try:
            result = tester.run_comprehensive_test(chunk_size=chunk_size)
            
            results.append({
                'chunk_size': chunk_size,
                'problems_found': result.total_problems_found,
                'processing_time': result.processing_time_seconds,
                'reference_match': result.reference_match_percentage,
                'character_similarity': result.detailed_comparison.get('character_similarity', 0)
            })
            
            print(f"✓ Chunk size {chunk_size}: {result.total_problems_found} problems, {result.processing_time_seconds:.1f}s, {result.reference_match_percentage:.1f}% match")
            
        except Exception as e:
            print(f"✗ Chunk size {chunk_size} failed: {e}")
            results.append({
                'chunk_size': chunk_size,
                'problems_found': 0,
                'processing_time': 999,
                'reference_match': 0,
                'character_similarity': 0,
                'error': str(e)
            })
    
    # Print comparison
    print("\n" + "="*60)
    print("CHUNK SIZE COMPARISON RESULTS")
    print("="*60)
    print(f"{'Chunk Size':<12} {'Problems':<10} {'Time(s)':<10} {'Match%':<8} {'CharSim%':<10}")
    print("-"*60)
    
    for result in results:
        if 'error' not in result:
            print(f"{result['chunk_size']:<12} {result['problems_found']:<10} {result['processing_time']:<10.1f} {result['reference_match']:<8.1f} {result['character_similarity']:<10.1f}")
        else:
            print(f"{result['chunk_size']:<12} ERROR: {result['error']}")
    
    return results

if __name__ == "__main__":
    test_chunk_sizes()