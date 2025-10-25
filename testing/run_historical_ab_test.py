#!/usr/bin/env python3
"""
Historical Configuration A/B Test Runner
Tests different configurations inspired by historical high-performing setup.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
import difflib

sys.path.insert(0, str(Path(__file__).parent.parent))

from md_processor import run_pipeline, get_default_config


class HistoricalABTest:
    """Test runner for historical-inspired configurations."""
    
    def __init__(self):
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.results_dir = Path(__file__).parent / "stress_test_results"
        self.test_file = self.test_data_dir / "tts_stress_test.md"
        self.reference_file = self.test_data_dir / "tts_stress_test_reference.md"
        
        # Load test files
        with open(self.test_file, 'r', encoding='utf-8') as f:
            self.test_input = f.read()
        with open(self.reference_file, 'r', encoding='utf-8') as f:
            self.reference_output = f.read()
    
    def test_configuration(self, name: str, config: Dict[str, Any], 
                          model: str, prompt_variant: str = None) -> Dict[str, Any]:
        """Test a specific configuration and return results."""
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"{'='*60}")
        print(f"Model: {model}")
        print(f"Chunk Size: {config['detector']['chunk_size']}")
        if prompt_variant:
            print(f"Prompt: {prompt_variant}")
        
        # Update prompts if using variant
        if prompt_variant:
            self.update_prompt(prompt_variant)
        
        try:
            # Run pipeline
            steps = ['mask', 'prepass-basic', 'prepass-advanced', 'detect', 'apply']
            result, stats = run_pipeline(
                self.test_input,
                steps=steps,
                config=config,
                llm_endpoint=config['detector']['api_base'],
                llm_model=model
            )
            
            # Calculate similarity
            similarity = self.calculate_similarity(result, self.reference_output)
            
            # Get corrections count
            detect_stats = stats.get('detect', {})
            apply_stats = stats.get('apply', {})
            
            print(f"\n✅ Test completed:")
            print(f"  Similarity: {similarity:.2%}")
            print(f"  Suggestions: {detect_stats.get('suggestions_valid', 0)}")
            print(f"  Applied: {apply_stats.get('replacements_applied', 0)}")
            print(f"  Rejected: {apply_stats.get('replacements_rejected', 0)}")
            
            # Save output
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.results_dir / f"ab_test_{name.replace(' ', '_')}_{timestamp}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            return {
                'success': True,
                'similarity': similarity,
                'stats': stats,
                'output_file': str(output_file),
                'output_length': len(result)
            }
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_similarity(self, output: str, reference: str) -> float:
        """Calculate similarity between output and reference."""
        seq_matcher = difflib.SequenceMatcher(None, output, reference)
        return seq_matcher.ratio()
    
    def update_prompt(self, variant: str):
        """Update prompts.json with a specific variant."""
        prompts_file = Path(__file__).parent.parent / "prompts.json"
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        if variant == "historical_style":
            prompts['detector']['prompt'] = """You are a TTS preprocessing detector working with English text. Find problematic patterns and suggest specific English replacements for better text-to-speech readability.

Analyze the text and return JSON with problem words AND their recommended TTS-friendly English replacements:

TARGET PATTERNS:
- Stylized/spaced letters: "F ʟ ᴀ s ʜ" → "Flash", "M ᴇ ɢ ᴀ" → "Mega"
- Small caps Unicode: "Bʏ Mʏ Rᴇsᴏʟᴠᴇ" → "By My Resolve"
- ALL-CAPS emphasis: "NO WAY" → "no way", "WHAT" → "what"
- ALL-CAPS screams: "AAAAAAA" → "aaa"
- Asterisk sounds: "*BANG!*" → "bang", "*crash*" → "crash"
- Repeated emphasis: "bluh... Bluh... BLUH!" → "bluh"
- Extended laughs: "Aaahahaha" → "haha"
- Chat log brackets: "[Username]:" → "Username:"
- Excessive punctuation: "!!!" → "!", "!?!?" → "!?"
- Nested parentheses: "(text (inner text))" → "text—inner text"

PRESERVE:
- Valid acronyms (NASA, GPU, API, HTTP, etc.)
- Code blocks and inline code
- Single punctuation marks
- Technical terms
- Proper nouns

IMPORTANT: All replacements must be in standard English. Use lowercase for emphasis normalization. Be aggressive with TTS improvements.

Return JSON only:
{"replacements": [{"find": "<exact_text>", "replace": "<tts_friendly_version>", "reason": "<type>"}]}

/no_think"""
        
        elif variant == "aggressive_tts":
            prompts['detector']['prompt'] = """TTS Aggressive Normalizer - Make text speak naturally.

AGGRESSIVE CORRECTIONS:
1. ALL-CAPS → lowercase: "NO WAY" → "no way", "STOP" → "stop"
2. Stylized Unicode → standard: "Bʏ" → "By", "ᴀ" → "a"
3. Sound effects → plain: "*BANG!*" → "bang", "CRASH" → "crash"
4. Repeats → single: "bluh... Bluh... BLUH" → "bluh"
5. Laughs → simple: "Aaahahaha" → "haha"
6. Screams → short: "AAAAAAA" → "aaa"
7. Brackets → clean: "[User]:" → "User:"
8. Multi-punct → single: "!!!" → "!", "!?!?" → "!?"
9. Letter space → word: "[M e g a]" → "[Mega]"
10. Nested parens → dashes: "(a (b))" → "a—b"

KEEP: Code, acronyms, proper nouns, single punctuation.

Be aggressive. Prioritize speakability over formatting.

Format: {"replacements": [{"find": "exact", "replace": "fixed", "reason": "type"}]}

/no_think"""
        
        # Save updated prompts
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
    
    def run_all_tests(self):
        """Run all A/B tests with different configurations."""
        print("="*60)
        print("HISTORICAL CONFIGURATION A/B TESTING")
        print("="*60)
        
        results = {}
        base_config = get_default_config()
        
        # Test 1: Current baseline (for comparison)
        print("\n📊 BASELINE TEST (Current Configuration)")
        current_config = base_config.copy()
        results['baseline_600_qwen3-8b'] = self.test_configuration(
            "Baseline Current",
            current_config,
            'qwen3-8b',
            None
        )
        
        # Test 2: Historical chunk size (8000)
        print("\n📊 TEST 1: Historical Chunk Size")
        config_8000 = base_config.copy()
        config_8000['detector']['chunk_size'] = 8000
        results['chunk_8000_qwen3-8b'] = self.test_configuration(
            "Chunk 8000",
            config_8000,
            'qwen3-8b',
            None
        )
        
        # Test 3: Historical prompt style
        print("\n📊 TEST 2: Historical Prompt Style")
        config_hist_prompt = base_config.copy()
        config_hist_prompt['detector']['chunk_size'] = 8000
        results['historical_prompt'] = self.test_configuration(
            "Historical Prompt",
            config_hist_prompt,
            'qwen3-8b',
            'historical_style'
        )
        
        # Test 4: Aggressive TTS prompt
        print("\n📊 TEST 3: Aggressive TTS Prompt")
        config_aggressive = base_config.copy()
        config_aggressive['detector']['chunk_size'] = 8000
        results['aggressive_tts'] = self.test_configuration(
            "Aggressive TTS",
            config_aggressive,
            'qwen3-8b',
            'aggressive_tts'
        )
        
        # Test 5: Try 4B model if available
        print("\n📊 TEST 4: 4B Instruct Model (if available)")
        config_4b = base_config.copy()
        config_4b['detector']['chunk_size'] = 8000
        results['qwen3-4b_instruct'] = self.test_configuration(
            "4B Instruct Model",
            config_4b,
            'qwen3-4b-instruct',
            'historical_style'
        )
        
        # Test 6: Relaxed validators
        print("\n📊 TEST 5: Relaxed Validators")
        config_relaxed = base_config.copy()
        config_relaxed['detector']['chunk_size'] = 8000
        config_relaxed['apply']['validators']['length_delta']['max_ratio'] = 0.05  # 5% vs 1%
        results['relaxed_validators'] = self.test_configuration(
            "Relaxed Validators",
            config_relaxed,
            'qwen3-8b',
            'aggressive_tts'
        )
        
        # Generate summary report
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results: Dict[str, Dict[str, Any]]):
        """Generate summary report of all tests."""
        print("\n" + "="*60)
        print("A/B TEST SUMMARY")
        print("="*60)
        
        # Sort by similarity
        sorted_results = sorted(
            [(name, res) for name, res in results.items() if res.get('success')],
            key=lambda x: x[1].get('similarity', 0),
            reverse=True
        )
        
        print("\n🏆 Rankings (by similarity):\n")
        for i, (name, res) in enumerate(sorted_results, 1):
            similarity = res.get('similarity', 0)
            stats = res.get('stats', {})
            detect = stats.get('detect', {})
            apply = stats.get('apply', {})
            
            print(f"{i}. {name}")
            print(f"   Similarity: {similarity:.2%}")
            print(f"   Suggestions: {detect.get('suggestions_valid', 0)}")
            print(f"   Applied: {apply.get('replacements_applied', 0)}")
            print()
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"ab_test_summary_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Historical Configuration A/B Test Results\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write("## Rankings\n\n")
            
            for i, (name, res) in enumerate(sorted_results, 1):
                f.write(f"### {i}. {name}\n\n")
                f.write(f"- **Similarity:** {res.get('similarity', 0):.2%}\n")
                f.write(f"- **Stats:**\n")
                f.write(f"```json\n{json.dumps(res.get('stats', {}), indent=2)}\n```\n\n")
        
        print(f"📄 Detailed report saved: {report_file.name}")


def main():
    """Main entry point."""
    tester = HistoricalABTest()
    results = tester.run_all_tests()
    
    # Return best similarity as exit code hint (0-100)
    best_similarity = max(
        (res.get('similarity', 0) for res in results.values() if res.get('success')),
        default=0
    )
    
    if best_similarity >= 0.65:  # Historical benchmark
        print("\n🎉 Matched or exceeded historical performance!")
        return 0
    elif best_similarity >= 0.60:
        print("\n✅ Good performance, close to historical benchmark")
        return 0
    else:
        print("\n⚠️  Below historical benchmark, more tuning needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
