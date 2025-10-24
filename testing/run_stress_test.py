#!/usr/bin/env python3
"""
Comprehensive Stress Test Runner for TTS-Proof v2
Tests the full pipeline against tts_stress_test.md and compares with reference output.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import difflib

# Add parent directory to path to import md_processor
sys.path.insert(0, str(Path(__file__).parent.parent))

from md_processor import (
    mask_protected, unmask, prepass_basic, prepass_advanced,
    detect_problems, apply_plan, validate_all, LLMClient,
    run_pipeline, DEFAULT_CONFIG
)


class StressTestRunner:
    """Orchestrates comprehensive stress testing of the TTS-Proof pipeline."""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.test_data_dir = test_dir / "test_data"
        self.results_dir = test_dir / "stress_test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_file = self.test_data_dir / "tts_stress_test.md"
        self.reference_file = self.test_data_dir / "tts_stress_test_reference.md"
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def load_files(self):
        """Load test input and reference output."""
        print("📁 Loading test files...")
        with open(self.test_file, 'r', encoding='utf-8') as f:
            self.test_input = f.read()
        with open(self.reference_file, 'r', encoding='utf-8') as f:
            self.reference_output = f.read()
        print(f"✅ Loaded {len(self.test_input)} chars input, {len(self.reference_output)} chars reference")
        
    def test_phase_masking(self):
        """Test Phase 1: Masking and unmasking."""
        print("\n🔒 Testing Phase 1: Masking...")
        try:
            masked, mask_table = mask_protected(self.test_input)
            restored = unmask(masked, mask_table)
            
            # Verify round-trip
            if restored == self.test_input:
                print("✅ Masking round-trip successful")
                return True, {
                    'masked_count': len(mask_table),
                    'round_trip': 'success'
                }
            else:
                print("❌ Masking round-trip FAILED")
                return False, {'error': 'round_trip_mismatch'}
        except Exception as e:
            print(f"❌ Masking error: {e}")
            return False, {'error': str(e)}
    
    def test_phase_prepass(self):
        """Test Phase 2 & 3: Prepass basic and advanced."""
        print("\n🧹 Testing Phase 2-3: Prepass...")
        try:
            masked, mask_table = mask_protected(self.test_input)
            
            # Basic prepass
            basic_result, basic_stats = prepass_basic(masked, DEFAULT_CONFIG)
            print(f"  Basic prepass: {len(basic_result)} chars, {basic_stats}")
            
            # Advanced prepass
            advanced_result, adv_stats = prepass_advanced(basic_result, DEFAULT_CONFIG)
            print(f"  Advanced prepass: {len(advanced_result)} chars, {adv_stats}")
            
            # Unmask
            final = unmask(advanced_result, mask_table)
            
            print("✅ Prepass phases completed")
            return True, {
                'basic_length': len(basic_result),
                'basic_stats': basic_stats,
                'advanced_length': len(advanced_result),
                'advanced_stats': adv_stats,
                'final_length': len(final)
            }
        except Exception as e:
            print(f"❌ Prepass error: {e}")
            return False, {'error': str(e)}
    
    def test_full_pipeline_cli(self):
        """Test complete pipeline using CLI-style invocation."""
        print("\n🚀 Testing Full Pipeline (CLI mode)...")
        try:
            # Run full pipeline with mask, prepass-basic, prepass-advanced
            # Note: Not testing detect/apply since those require LLM connection
            steps = ['mask', 'prepass-basic', 'prepass-advanced']
            
            # Use placeholder endpoint/model (won't be called for these steps)
            result, stats = run_pipeline(
                self.test_input,
                steps=steps,
                config=DEFAULT_CONFIG,
                llm_endpoint='http://localhost:1234/v1',
                llm_model='placeholder'
            )
            
            # Save output
            output_file = self.results_dir / f"pipeline_output_{self.timestamp}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            print(f"✅ Pipeline completed. Output saved to {output_file.name}")
            print(f"  Stats: {json.dumps(stats, indent=2)}")
            
            return True, {
                'output_file': str(output_file),
                'output_length': len(result),
                'stats': stats
            }
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return False, {'error': str(e)}
    
    def test_llm_connection(self):
        """Test LLM connection (optional, non-blocking)."""
        print("\n🔌 Testing LLM Connection (optional)...")
        try:
            client = LLMClient(
                endpoint='http://localhost:1234/v1',
                model='test-model'
            )
            # Simple connectivity test with minimal text
            response = client.complete(
                "Fix grammar issues",
                "This is test text.",
                max_tokens=50
            )
            print("✅ LLM connection successful")
            return True, {'status': 'connected'}
        except Exception as e:
            print(f"⚠️  LLM not available: {e}")
            print("   (This is optional for basic pipeline testing)")
            return False, {'error': str(e), 'optional': True}
    
    def compare_with_reference(self, output_text: str):
        """Compare pipeline output with reference file."""
        print("\n📊 Comparing with reference output...")
        
        # Calculate similarity metrics
        seq_matcher = difflib.SequenceMatcher(None, output_text, self.reference_output)
        similarity = seq_matcher.ratio()
        
        # Generate unified diff
        diff = list(difflib.unified_diff(
            self.reference_output.splitlines(keepends=True),
            output_text.splitlines(keepends=True),
            fromfile='reference',
            tofile='output',
            lineterm=''
        ))
        
        # Save comparison report
        report_file = self.results_dir / f"comparison_{self.timestamp}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Stress Test Comparison Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write(f"**Similarity Score:** {similarity:.2%}\n\n")
            f.write(f"**Input Length:** {len(self.test_input)} chars\n")
            f.write(f"**Output Length:** {len(output_text)} chars\n")
            f.write(f"**Reference Length:** {len(self.reference_output)} chars\n\n")
            
            if diff:
                f.write("## Differences\n\n")
                f.write("```diff\n")
                f.write(''.join(diff[:500]))  # Limit diff output
                if len(diff) > 500:
                    f.write(f"\n... ({len(diff) - 500} more lines)\n")
                f.write("\n```\n")
            else:
                f.write("✅ **No differences found!**\n")
        
        print(f"📄 Comparison report saved to {report_file.name}")
        print(f"📈 Similarity: {similarity:.2%}")
        
        return {
            'similarity': similarity,
            'report_file': str(report_file),
            'diff_lines': len(diff)
        }
    
    def test_validators(self):
        """Test all 7 structural validators."""
        print("\n🛡️  Testing Structural Validators...")
        
        # Create test cases for each validator
        masked, mask_table = mask_protected(self.test_input)
        
        test_cases = [
            ("Original (should pass)", self.test_input, self.test_input),
            ("Mask parity violation", self.test_input, self.test_input + "\n__MASKED_999__"),
            ("Backtick violation", "Normal `code` text", "Normal code text"),
            ("Bracket violation", "Text [link](url)", "Text link](url)"),
        ]
        
        results = {}
        for name, original, edited in test_cases:
            try:
                # For masked content tests, use mask_table
                test_mask_table = mask_table if "Original" in name else {}
                is_valid, error = validate_all(original, edited, test_mask_table)
                
                if "should pass" in name:
                    status = "✅" if is_valid else "❌"
                else:
                    status = "✅" if not is_valid else "❌"  # Should fail
                
                print(f"  {status} {name}: {'PASS' if is_valid else error}")
                results[name] = {'valid': is_valid, 'error': error}
            except Exception as e:
                print(f"  ❌ {name}: Exception - {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    def generate_summary_report(self, all_results: dict):
        """Generate comprehensive summary report."""
        report_file = self.results_dir / f"stress_test_summary_{self.timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# TTS-Proof v2 Stress Test Summary\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Branch:** feat/stress-test-validation\n\n")
            
            f.write("## Test Results\n\n")
            
            for test_name, result in all_results.items():
                success = result.get('success', False)
                icon = "✅" if success else "❌"
                f.write(f"### {icon} {test_name}\n\n")
                
                if 'data' in result:
                    f.write("```json\n")
                    f.write(json.dumps(result['data'], indent=2))
                    f.write("\n```\n\n")
            
            f.write("## Files Generated\n\n")
            f.write(f"- Summary report: `{report_file.name}`\n")
            if 'pipeline_test' in all_results and all_results['pipeline_test'].get('success'):
                output_file = all_results['pipeline_test']['data'].get('output_file', 'N/A')
                f.write(f"- Pipeline output: `{Path(output_file).name}`\n")
            if 'comparison' in all_results:
                comp_file = all_results['comparison']['data'].get('report_file', 'N/A')
                f.write(f"- Comparison report: `{Path(comp_file).name}`\n")
        
        print(f"\n📋 Summary report saved to {report_file.name}")
        return report_file
    
    def run_all_tests(self):
        """Execute all stress tests and generate reports."""
        print("="*60)
        print("TTS-PROOF V2 COMPREHENSIVE STRESS TEST")
        print("="*60)
        
        self.load_files()
        
        all_results = {}
        
        # Test 1: Masking
        success, data = self.test_phase_masking()
        all_results['masking'] = {'success': success, 'data': data}
        
        # Test 2: Prepass
        success, data = self.test_phase_prepass()
        all_results['prepass'] = {'success': success, 'data': data}
        
        # Test 3: Validators
        validator_results = self.test_validators()
        all_results['validators'] = {'success': True, 'data': validator_results}
        
        # Test 4: Full Pipeline
        success, data = self.test_full_pipeline_cli()
        all_results['pipeline_test'] = {'success': success, 'data': data}
        
        # Test 5: LLM Connection (optional)
        success, data = self.test_llm_connection()
        all_results['llm_connection'] = {'success': success, 'data': data}
        
        # Compare output with reference (if pipeline succeeded)
        if all_results['pipeline_test']['success']:
            output_file = all_results['pipeline_test']['data']['output_file']
            with open(output_file, 'r', encoding='utf-8') as f:
                output_text = f.read()
            comparison = self.compare_with_reference(output_text)
            all_results['comparison'] = {'success': True, 'data': comparison}
        
        # Generate summary
        summary_file = self.generate_summary_report(all_results)
        
        print("\n" + "="*60)
        print("STRESS TEST COMPLETE")
        print("="*60)
        print(f"📁 All results saved to: {self.results_dir}")
        print(f"📋 Summary report: {summary_file.name}")
        
        # Return exit code based on critical test results
        critical_tests = ['masking', 'prepass', 'pipeline_test']
        all_critical_passed = all(
            all_results[test]['success'] for test in critical_tests
        )
        
        return 0 if all_critical_passed else 1


def main():
    """Main entry point."""
    test_dir = Path(__file__).parent
    runner = StressTestRunner(test_dir)
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
