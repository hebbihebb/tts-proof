#!/usr/bin/env python3
"""
Prompt Optimization Tool for TTS-Proof v2
Iteratively tests detector prompts and tracks performance metrics.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from md_processor import run_pipeline, DEFAULT_CONFIG


class PromptOptimizer:
    """Manages iterative prompt testing and optimization."""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.test_data_dir = test_dir / "test_data"
        self.results_dir = test_dir / "prompt_optimization_results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_file = self.test_data_dir / "tts_stress_test.md"
        self.reference_file = self.test_data_dir / "tts_stress_test_reference.md"
        self.prompts_file = Path(__file__).parent.parent / "prompts.json"
        
        # Load test data
        with open(self.test_file, 'r', encoding='utf-8') as f:
            self.test_input = f.read()
        with open(self.reference_file, 'r', encoding='utf-8') as f:
            self.reference_output = f.read()
        
        # Load current prompts
        with open(self.prompts_file, 'r', encoding='utf-8') as f:
            self.prompts_config = json.load(f)
        
        self.iteration = 0
        self.results_log = []
    
    def backup_prompts(self):
        """Backup current prompts file."""
        backup_file = self.results_dir / f"prompts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(self.prompts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📦 Backed up prompts to {backup_file.name}")
    
    def update_detector_prompt(self, new_prompt: str):
        """Update the detector prompt in prompts.json."""
        self.prompts_config['detector']['prompt'] = new_prompt
        with open(self.prompts_file, 'w', encoding='utf-8') as f:
            json.dump(self.prompts_config, f, indent=2)
        print(f"✏️  Updated detector prompt")
    
    def run_test(self, prompt_name: str) -> Dict:
        """Run pipeline test and collect metrics."""
        self.iteration += 1
        print(f"\n{'='*60}")
        print(f"ITERATION {self.iteration}: {prompt_name}")
        print(f"{'='*60}")
        
        try:
            # Run pipeline with LLM phases
            result, stats = run_pipeline(
                self.test_input,
                steps=['mask', 'prepass-basic', 'prepass-advanced', 'detect', 'apply'],
                config=DEFAULT_CONFIG,
                llm_endpoint='http://localhost:1234/v1',
                llm_model='qwen3-8b'
            )
            
            # Calculate similarity
            import difflib
            seq_matcher = difflib.SequenceMatcher(None, result, self.reference_output)
            similarity = seq_matcher.ratio()
            
            # Extract key metrics
            detect_stats = stats.get('detect', {})
            apply_stats = stats.get('apply', {})
            
            metrics = {
                'iteration': self.iteration,
                'prompt_name': prompt_name,
                'timestamp': datetime.now().isoformat(),
                'similarity': similarity * 100,
                'output_length': len(result),
                'suggestions_valid': detect_stats.get('suggestions_valid', 0),
                'suggestions_rejected': detect_stats.get('suggestions_rejected', 0),
                'plan_size': detect_stats.get('plan_size', 0),
                'replacements_applied': apply_stats.get('replacements_applied', 0),
                'replacements_rejected': apply_stats.get('replacements_rejected', 0),
                'validation_passed': apply_stats.get('validation_passed', False),
                'stats': stats
            }
            
            # Save output
            output_file = self.results_dir / f"iter_{self.iteration:02d}_{prompt_name.replace(' ', '_')}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"\n📊 Results:")
            print(f"   Similarity: {metrics['similarity']:.2f}%")
            print(f"   Suggestions: {metrics['suggestions_valid']} valid, {metrics['suggestions_rejected']} rejected")
            print(f"   Applied: {metrics['replacements_applied']}")
            print(f"   Output saved: {output_file.name}")
            
            self.results_log.append(metrics)
            return metrics
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                'iteration': self.iteration,
                'prompt_name': prompt_name,
                'error': str(e),
                'similarity': 0
            }
    
    def save_results_summary(self):
        """Save comprehensive results summary."""
        summary_file = self.results_dir / f"optimization_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            'test_info': {
                'test_file': str(self.test_file),
                'reference_file': str(self.reference_file),
                'total_iterations': self.iteration,
                'timestamp': datetime.now().isoformat()
            },
            'results': self.results_log,
            'best_result': max(self.results_log, key=lambda x: x.get('similarity', 0)) if self.results_log else None
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📋 Summary saved to {summary_file.name}")
        
        # Print comparison table
        print(f"\n{'='*80}")
        print("OPTIMIZATION RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"{'Iter':<6} {'Prompt':<30} {'Similarity':<12} {'Suggestions':<12} {'Applied':<10}")
        print(f"{'-'*80}")
        
        for result in self.results_log:
            if 'error' not in result:
                print(f"{result['iteration']:<6} {result['prompt_name'][:28]:<30} "
                      f"{result['similarity']:>10.2f}% {result['suggestions_valid']:>11} "
                      f"{result['replacements_applied']:>9}")
        
        if summary['best_result']:
            best = summary['best_result']
            print(f"\n🏆 BEST RESULT: {best['prompt_name']} ({best['similarity']:.2f}% similarity)")
    
    def run_optimization(self, prompt_variations: List[Tuple[str, str]]):
        """Run optimization with list of prompt variations."""
        print("🔬 Starting Prompt Optimization")
        print(f"   Test file: {self.test_file.name}")
        print(f"   Reference: {self.reference_file.name}")
        print(f"   Variations to test: {len(prompt_variations)}")
        
        # Backup original prompts
        self.backup_prompts()
        
        # Test each variation
        for prompt_name, prompt_text in prompt_variations:
            self.update_detector_prompt(prompt_text)
            self.run_test(prompt_name)
        
        # Save summary
        self.save_results_summary()
        
        # Restore best prompt
        if self.results_log:
            best = max(self.results_log, key=lambda x: x.get('similarity', 0))
            best_idx = best['iteration'] - 1
            best_prompt = prompt_variations[best_idx][1]
            self.update_detector_prompt(best_prompt)
            print(f"\n✅ Applied best prompt: {best['prompt_name']}")


# Define prompt variations to test
PROMPT_VARIATIONS = [
    (
        "Baseline (Unicode Only)",
        """Find stylized Unicode letters and normalize to standard English. Return JSON only.

Examples:
"Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!"  
"Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!" → "Spiral Seekers!"
"[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip: normal text, usernames, punctuation, code.

Format:
{"replacements": [{"find": "text", "replace": "fixed", "reason": "unicode"}]}

/no_think"""
    ),
    (
        "Comprehensive TTS v1",
        """You are a TTS-readability detector. Find and fix text that would sound bad when read aloud by text-to-speech.

DETECT AND FIX:
1. Stylized Unicode: "Bʏ" → "By", "Sᴘɪʀᴀʟ" → "Spiral"
2. Chat brackets: "[Username]:" → "Username:"
3. All-caps emphasis: "NO WAY!" → "no way!", "BANG" → "bang"
4. Letter spacing: "[M e g a]" → "[Mega]"
5. Excessive punctuation: "!!!" → "!", "???" → "?"
6. Multiple ellipsis: "..." (keep as-is, but fix "....." to "...")

PRESERVE:
- Code blocks and inline code
- Normal capitalization (proper nouns, sentence starts)
- Markdown structure
- Single punctuation marks

Return JSON only:
{"replacements": [{"find": "exact text", "replace": "fixed text", "reason": "issue type"}]}

/no_think"""
    ),
    (
        "Comprehensive TTS v2",
        """Detect TTS-problematic patterns in Markdown. Fix patterns that would sound unnatural when read aloud.

TARGET PATTERNS:
• Stylized Unicode → Standard letters ("Bʏ" → "By", "Rᴇsᴏʟᴠᴇ" → "Resolve")
• Chat log brackets → Plain format ("[Username]:" → "Username:")
• All-caps words → Lowercase (unless proper noun) ("BANG" → "bang", "NO WAY" → "no way")
• Letter-spaced text → Normal spacing ("[M e g a]" → "[Mega]")
• Excessive punctuation → Single ("!!!" → "!", "???" → "?", "!?!?" → "?")
• Repeated emphasis → Single ("ugh ugh ugh" → "ugh")

SKIP:
✓ Code blocks (```) and inline code (`)
✓ Proper nouns and acronyms (NASA, API)
✓ Markdown syntax
✓ Normal punctuation
✓ Standard ellipsis (...)

Output format:
{"replacements": [{"find": "exact original text", "replace": "corrected text", "reason": "brief reason"}]}

Be aggressive - fix all TTS issues you find.

/no_think"""
    ),
    (
        "Comprehensive TTS v3",
        """TTS Problem Detector - Find text patterns that sound bad when read aloud by text-to-speech engines.

FIX THESE PATTERNS:
1. Unicode Stylization
   "Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!"
   "Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs" → "Spiral Seekers"
   "Hᴏɴᴏʀɪɴɢ Vᴀɴɢᴜᴀʀᴅ" → "Honoring Vanguard"

2. Chat Log Formatting
   "[MeanBeanMachine]:" → "MeanBeanMachine:"
   "[Username123]:" → "Username123:"

3. All-Caps Emphasis (except proper nouns/acronyms)
   "NO WAY!" → "no way!"
   "AAAAAAA stop" → "stop"
   "BANG!" → "bang!"
   "WHAT!?!?!?" → "What?"
   Keep: NASA, API, GPU (known acronyms)

4. Letter-Spaced Text
   "[M ᴇ ɢ ᴀ B u s t e r]" → "[Mega Buster]"
   "M e g a" → "Mega"

5. Excessive Punctuation
   "what!?!?!?" → "what?"
   "really!!!" → "really!"
   "huh???" → "huh?"

6. Repeated Words
   "bluh... Bluh... BLUH!" → "bluh"
   "so so so weird" → "so weird"

NEVER TOUCH:
- Code blocks (``` or `)
- Markdown links/images
- Proper sentence capitalization
- Valid acronyms
- Normal punctuation (single !, ?, .)
- Ellipsis (...)

Return ONLY valid JSON:
{"replacements": [{"find": "exact text from input", "replace": "corrected version", "reason": "pattern type"}]}

Find ALL instances. Be thorough.

/no_think"""
    ),
    (
        "Ultra-Aggressive v1",
        """TTS Normalizer - Make text perfect for text-to-speech by fixing ALL problematic patterns.

AGGRESSIVE FIXES:
✓ Stylized Unicode: Any non-ASCII letter → ASCII equivalent
✓ Chat brackets: Remove ALL "[...]:" patterns at line start
✓ All-caps words: Convert to lowercase (except: NASA, GPU, API, CPU, RAM, USB, HTTP, HTTPS, URL)
✓ Letter spacing: Remove extra spaces between letters
✓ Excessive punct: "!!!" "???" "!?!?" → single punctuation
✓ Repeated patterns: "ugh ugh ugh" → "ugh", "bluh... Bluh... BLUH" → "bluh"
✓ Multiple exclamations: "Luna!!!" → "Luna!"
✓ Question chains: "what!?!?" → "what?"

EXAMPLES:
"Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!"
"[MeanBeanMachine]: Luna!!!" → "MeanBeanMachine: Luna!"
"NO WAY!" → "no way!"
"*BANG!*" → "*bang*"
"AAAAAAA stop" → "stop"
"[M ᴇ ɢ ᴀ B u s t e r]" → "[Mega Buster]"
"what!?!?!?" → "what?"
"bluh... Bluh... BLUH!" → "bluh"

PROTECTED:
- Code blocks/inline code
- Markdown structure
- Links and images
- Ellipsis "..."
- Proper sentence capitals
- Known acronyms

Output JSON:
{"replacements": [{"find": "exact match", "replace": "fixed", "reason": "type"}]}

Maximum corrections. Be thorough.

/no_think"""
    )
]


def main():
    """Main entry point."""
    test_dir = Path(__file__).parent
    optimizer = PromptOptimizer(test_dir)
    optimizer.run_optimization(PROMPT_VARIATIONS)


if __name__ == "__main__":
    main()
