#!/usr/bin/env python3
"""
Fast Prepass-Only Testing System

Runs only the TTS prepass detection phase for rapid iteration and optimization.
Skips grammar correction to focus on improving TTS problem detection quality.
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import difflib
import re
from dataclasses import dataclass

# Import our TTS-Proof modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from md_proof import call_lmstudio, chunk_paragraphs, mask_urls, unmask_urls, extract_between_sentinels
from prepass import run_prepass, detect_tts_problems, DETECTOR_PROMPT

@dataclass
class PrepassTestResult:
    """Container for prepass-only test results"""
    timestamp: str
    network_api_base: str
    model_name: str
    prepass_prompt_version: str
    total_problems_found: int
    chunks_processed: int
    processing_time_seconds: float
    detection_accuracy: float
    detailed_analysis: Dict
    log_file: str

class PrepassOnlyTester:
    """Fast prepass-only testing system"""
    
    def __init__(self, network_api_base: str = "http://192.168.8.104:1234/v1", 
                 model: str = "qwen3-8b"):
        self.network_api_base = network_api_base
        self.model = model
        test_data_dir = Path(__file__).parent.parent / "test_data"
        self.test_file = test_data_dir / "tts_stress_test.md"
        self.reference_file = test_data_dir / "tts_stress_test_reference.md"
        root_dir = Path(__file__).parent.parent.parent
        self.results_dir = Path(__file__).parent.parent / "prepass_test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Load prompts
        self.prepass_prompt = (root_dir / "prepass_prompt.txt").read_text(encoding='utf-8')
        
    def validate_network(self) -> bool:
        """Check if network server is accessible"""
        try:
            response = requests.get(f"{self.network_api_base.rstrip('/v1')}/v1/models", timeout=10)
            if response.status_code == 200:
                models = response.json().get('data', [])
                print(f"✓ Network server accessible. Available models: {len(models)}")
                return True
        except Exception as e:
            print(f"❌ Network server not accessible: {e}")
            return False
    
    def run_prepass_only(self) -> Tuple[str, Dict, float]:
        """Run only the prepass detection phase"""
        print("\n--- Running Prepass Detection Only ---")
        
        # Run prepass on the test file
        start_time = time.time()
        prepass_report = run_prepass(
            input_path=self.test_file,
            api_base=self.network_api_base,
            model=self.model,
            chunk_chars=8000,
            show_progress=True
        )
        prepass_time = time.time() - start_time
        
        # Read the processed content (prepass returns report, need to reconstruct text)
        # For testing, we'll load the original and apply replacements
        test_content = self.test_file.read_text(encoding='utf-8')
        result_content = self._apply_prepass_fixes(test_content, prepass_report)
        
        print(f"✓ Prepass completed in {prepass_time:.2f}s")
        
        return result_content, prepass_report, prepass_time
    
    def _apply_prepass_fixes(self, text: str, prepass_report: Dict) -> str:
        """Apply prepass replacements to text"""
        result = text
        for chunk in prepass_report.get('chunks', []):
            for replacement in chunk.get('replacements', []):
                find_text = replacement.get('find', '')
                replace_text = replacement.get('replace', '')
                if find_text and find_text != replace_text:
                    result = result.replace(find_text, replace_text)
        return result
    
    def analyze_prepass_quality(self, result_content: str, prepass_report: Dict) -> Dict:
        """Analyze the quality of TTS detection"""
        reference_content = self.reference_file.read_text(encoding='utf-8')
        
        # Count actual TTS problems found
        total_replacements = sum(
            len(chunk.get('replacements', [])) 
            for chunk in prepass_report.get('chunks', [])
        )
        
        # Filter only actual fixes (not skips)
        actual_fixes = []
        for chunk in prepass_report.get('chunks', []):
            for replacement in chunk.get('replacements', []):
                if replacement['find'] != replacement['replace']:
                    actual_fixes.append(replacement)
        
        # Compare result with reference
        result_lines = result_content.strip().split('\n')
        reference_lines = reference_content.strip().split('\n')
        
        matcher = difflib.SequenceMatcher(None, result_lines, reference_lines)
        similarity = matcher.ratio()
        
        # Calculate line-by-line accuracy
        matching_lines = 0
        total_lines = len(reference_lines)
        for i, ref_line in enumerate(reference_lines):
            if i < len(result_lines) and result_lines[i].strip() == ref_line.strip():
                matching_lines += 1
        
        line_accuracy = (matching_lines / total_lines * 100) if total_lines > 0 else 0
        
        return {
            'total_replacements': total_replacements,
            'actual_fixes': len(actual_fixes),
            'similarity_ratio': similarity,
            'line_accuracy': line_accuracy,
            'matching_lines': matching_lines,
            'total_lines': total_lines,
            'fixes_detail': actual_fixes
        }
    
    def run_test(self) -> PrepassTestResult:
        """Execute a complete prepass-only test"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("=== Fast Prepass-Only Test ===")
        print(f"Network API: {self.network_api_base}")
        print(f"Model: {self.model}")
        
        # Validate network
        if not self.validate_network():
            raise Exception("Network server not accessible")
        
        # Run prepass
        result_content, prepass_report, prepass_time = self.run_prepass_only()
        
        # Analyze quality
        print("\n--- Analyzing Detection Quality ---")
        analysis = self.analyze_prepass_quality(result_content, prepass_report)
        
        print(f"\n=== Test Complete ===")
        print(f"Prepass time: {prepass_time:.2f}s")
        print(f"Problems found: {analysis['actual_fixes']}")
        print(f"Line accuracy: {analysis['line_accuracy']:.1f}%")
        print(f"Similarity ratio: {analysis['similarity_ratio']*100:.1f}%")
        
        # Save detailed log
        log_file = self.results_dir / f"prepass_test_log_{timestamp}.md"
        self._write_log(log_file, prepass_time, analysis, prepass_report)
        
        print(f"\n📁 Log saved to: {log_file}")
        
        return PrepassTestResult(
            timestamp=timestamp,
            network_api_base=self.network_api_base,
            model_name=self.model,
            prepass_prompt_version=self.prepass_prompt[:100],
            total_problems_found=analysis['actual_fixes'],
            chunks_processed=len(prepass_report.get('chunks', [])),
            processing_time_seconds=prepass_time,
            detection_accuracy=analysis['line_accuracy'],
            detailed_analysis=analysis,
            log_file=str(log_file)
        )
    
    def _write_log(self, log_file: Path, prepass_time: float, analysis: Dict, prepass_report: Dict):
        """Write detailed test log"""
        log_content = f"""# Fast Prepass-Only Test Log

**Network API:** {self.network_api_base}
**Model:** {self.model}
**Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Performance Metrics

- **Prepass Time:** {prepass_time:.2f}s
- **Problems Found:** {analysis['actual_fixes']}
- **Line Accuracy:** {analysis['line_accuracy']:.1f}%
- **Similarity Ratio:** {analysis['similarity_ratio']*100:.1f}%
- **Matching Lines:** {analysis['matching_lines']}/{analysis['total_lines']}

## Prepass Prompt Used

```
{self.prepass_prompt}
```

## Problems Detected

```json
{json.dumps(analysis['fixes_detail'], indent=2)}
```

## Full Prepass Report

```json
{json.dumps(prepass_report, indent=2)}
```
"""
        log_file.write_text(log_content, encoding='utf-8')

def main():
    """Run the fast prepass-only test"""
    tester = PrepassOnlyTester(
        network_api_base="http://192.168.8.104:1234/v1",
        model="qwen3-8b"
    )
    
    try:
        result = tester.run_test()
        print("\n🎉 Prepass-only test completed successfully!")
        print(f"📊 Detection accuracy: {result.detection_accuracy:.1f}%")
        print(f"📁 Detailed log: {result.log_file}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
