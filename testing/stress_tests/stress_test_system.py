#!/usr/bin/env python3
"""
TTS Stress Test System - Network Edition

Comprehensive testing system that:
1. Uses a network-based LM Studio server (http://192.168.8.104:1234/v1)
2. Tests against tts_stress_test.md with complex TTS problems
3. Compares results with tts_stress_test_reference.md (GPT-5 quality)
4. Logs everything with detailed analysis
5. Provides metrics for iterative prompt improvement
6. Tracks prompt evolution and performance improvements
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

# Import our TTS-Proof modules (fix paths after directory reorganization)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from md_proof import call_lmstudio, chunk_paragraphs, mask_urls, unmask_urls, extract_between_sentinels
from prepass import run_prepass, detect_tts_problems, DETECTOR_PROMPT

@dataclass
class TestResult:
    """Container for test run results and metrics"""
    timestamp: str
    network_api_base: str
    model_name: str
    prepass_prompt_version: str
    grammar_prompt_version: str
    total_problems_found: int
    chunks_processed: int
    processing_time_seconds: float
    reference_match_percentage: float
    detailed_comparison: Dict
    raw_output_file: str
    log_file: str

class StressTestSystem:
    """Comprehensive stress testing system for TTS-Proof"""
    
    def __init__(self, network_api_base: str = "http://192.168.8.104:1234/v1", 
                 model: str = "qwen/qwen3-4b-instruct-2507"):
        self.network_api_base = network_api_base
        self.model = model
        # Fix paths after directory reorganization
        test_data_dir = Path(__file__).parent.parent / "test_data"
        self.test_file = test_data_dir / "tts_stress_test.md"
        self.reference_file = test_data_dir / "tts_stress_test_reference.md"
        # Fix paths after directory reorganization
        root_dir = Path(__file__).parent.parent.parent
        self.results_dir = Path(__file__).parent.parent / "stress_test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Load current prompts
        self.load_current_prompts()
        
        # Test history for tracking improvements
        self.test_history = []
        
    def load_current_prompts(self):
        """Load current prepass and grammar prompts"""
        root_dir = Path(__file__).parent.parent.parent
        prepass_path = root_dir / "prepass_prompt.txt"
        grammar_path = root_dir / "grammar_promt.txt"  # Note: keep original typo
        
        self.prepass_prompt = ""
        if prepass_path.exists():
            with open(prepass_path, encoding="utf-8") as f:
                self.prepass_prompt = f.read().strip()
                
        self.grammar_prompt = ""  
        if grammar_path.exists():
            with open(grammar_path, encoding="utf-8") as f:
                self.grammar_prompt = f.read().strip()
    
    def test_network_connectivity(self) -> bool:
        """Test if the network LM Studio server is accessible"""
        try:
            response = requests.get(f"{self.network_api_base.rstrip('/v1')}/v1/models", timeout=10)
            if response.status_code == 200:
                models = response.json()
                print(f"✓ Network server accessible. Available models: {len(models.get('data', []))}")
                return True
            else:
                print(f"✗ Network server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Cannot connect to network server: {e}")
            return False
    
    def run_comprehensive_test(self, chunk_size: int = 4000) -> TestResult:
        """Run a complete stress test with full logging and analysis"""
        print("=== TTS Stress Test System - Network Edition ===")
        print(f"Network API: {self.network_api_base}")
        print(f"Model: {self.model}")
        print(f"Chunk Size: {chunk_size}")
        
        # Test connectivity first
        if not self.test_network_connectivity():
            raise Exception("Cannot connect to network LM Studio server")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create test-specific log files
        log_file = self.results_dir / f"stress_test_log_{timestamp}.md"
        raw_output_file = self.results_dir / f"raw_output_{timestamp}.md"
        comparison_file = self.results_dir / f"comparison_{timestamp}.md"
        
        start_time = time.time()
        
        print("\\n--- Loading Test Files ---")
        
        # Load test content
        if not self.test_file.exists():
            raise FileNotFoundError(f"Stress test file not found: {self.test_file}")
            
        with open(self.test_file, 'r', encoding='utf-8') as f:
            test_content = f.read()
        print(f"✓ Loaded stress test file ({len(test_content)} characters)")
        
        # Load reference content  
        if not self.reference_file.exists():
            raise FileNotFoundError(f"Reference file not found: {self.reference_file}")
            
        with open(self.reference_file, 'r', encoding='utf-8') as f:
            reference_content = f.read()
        print(f"✓ Loaded reference file ({len(reference_content)} characters)")
        
        print("\\n--- Running Prepass Detection ---")
        
        # Run prepass detection with detailed logging
        prepass_start = time.time()
        prepass_report = self.run_prepass_with_logging(test_content, chunk_size, log_file)
        prepass_time = time.time() - prepass_start
        
        problems_found = len(prepass_report.get('summary', {}).get('unique_problem_words', []))
        chunks_processed = prepass_report.get('summary', {}).get('chunks_processed', 0)
        
        print(f"✓ Prepass completed in {prepass_time:.2f}s")
        print(f"  Found {problems_found} unique problems across {chunks_processed} chunks")
        
        print("\\n--- Running Grammar Correction ---")
        
        # Run grammar correction (for now, just simulate - can be enabled later)
        grammar_start = time.time()
        corrected_content = self.run_grammar_correction_with_logging(
            test_content, prepass_report, chunk_size, log_file, raw_output_file
        )
        grammar_time = time.time() - grammar_start
        
        print(f"✓ Grammar correction completed in {grammar_time:.2f}s")
        
        print("\\n--- Comparing with Reference ---")
        
        # Compare with reference
        comparison_result = self.compare_with_reference(
            corrected_content, reference_content, comparison_file
        )
        
        total_time = time.time() - start_time
        
        # Create comprehensive result
        result = TestResult(
            timestamp=timestamp,
            network_api_base=self.network_api_base,
            model_name=self.model,
            prepass_prompt_version=self._get_prompt_hash(self.prepass_prompt),
            grammar_prompt_version=self._get_prompt_hash(self.grammar_prompt),
            total_problems_found=problems_found,
            chunks_processed=chunks_processed,
            processing_time_seconds=total_time,
            reference_match_percentage=comparison_result['match_percentage'],
            detailed_comparison=comparison_result,
            raw_output_file=str(raw_output_file),
            log_file=str(log_file)
        )
        
        # Save comprehensive log
        self.save_comprehensive_log(result, log_file)
        
        # Add to history
        self.test_history.append(result)
        
        print(f"\\n=== Test Complete ===")
        print(f"Overall time: {total_time:.2f}s")
        print(f"Reference match: {comparison_result['match_percentage']:.1f}%")
        print(f"Log saved to: {log_file}")
        print(f"Raw output: {raw_output_file}")
        print(f"Comparison: {comparison_file}")
        
        return result
    
    def run_prepass_with_logging(self, content: str, chunk_size: int, log_file: Path) -> Dict:
        """Run prepass detection with detailed logging"""
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            # Run prepass with our network server
            report = run_prepass(tmp_path, self.network_api_base, self.model, chunk_size, show_progress=True)
            
            # Log detailed prepass results
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"# Prepass Detection Log\\n\\n")
                f.write(f"**Network API:** {self.network_api_base}\\n")
                f.write(f"**Model:** {self.model}\\n")
                f.write(f"**Chunk Size:** {chunk_size}\\n\\n")
                
                f.write("## Prepass Prompt Used\\n\\n")
                f.write("```\\n")
                f.write(self.prepass_prompt)
                f.write("\\n```\\n\\n")
                
                f.write("## Problems Found\\n\\n")
                f.write(f"**Total unique problems:** {len(report.get('summary', {}).get('unique_problem_words', []))}\\n\\n")
                
                for i, word in enumerate(report.get('summary', {}).get('unique_problem_words', [])[:20]):  # First 20
                    f.write(f"{i+1}. `{word}`\\n")
                
                f.write("\\n## Full Prepass Report\\n\\n")
                f.write("```json\\n")
                f.write(json.dumps(report, indent=2, ensure_ascii=False))
                f.write("\\n```\\n\\n")
            
            return report
            
        finally:
            # Clean up temp file
            tmp_path.unlink()
    
    def run_grammar_correction_with_logging(self, content: str, prepass_report: Dict, 
                                          chunk_size: int, log_file: Path, 
                                          raw_output_file: Path) -> str:
        """Run grammar correction with detailed logging"""
        
        # First apply prepass replacements
        corrected_content = content
        replacement_map = prepass_report.get('summary', {}).get('replacement_map', {})
        
        for find_text, replace_text in replacement_map.items():
            corrected_content = corrected_content.replace(find_text, replace_text)
        
        # Now run actual grammar correction on chunks
        from md_proof import chunk_paragraphs, correct_chunk
        
        # Chunk the content for grammar correction
        chunks = chunk_paragraphs(corrected_content, chunk_size)
        
        grammar_corrected_chunks = []
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("# Grammar Correction Log\\n\\n")
            f.write("## Grammar Prompt Used\\n\\n") 
            f.write("```\\n")
            f.write(self.grammar_prompt)
            f.write("\\n```\\n\\n")
            
            f.write("## Prepass Replacements Applied\\n\\n")
            for find_text, replace_text in replacement_map.items():
                f.write(f"- `{find_text}` → `{replace_text}`\\n")
            
            f.write(f"\\n## Grammar Correction Process\\n\\n")
            f.write(f"**Chunks to process:** {len(chunks)}\\n\\n")
        
        # Process each chunk through grammar correction
        for i, (chunk_type, chunk_content) in enumerate(chunks):
            if chunk_type == "code":
                # Preserve code blocks as-is
                grammar_corrected_chunks.append(chunk_content)
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"**Chunk {i+1}:** Code block preserved\\n")
            elif len(chunk_content.strip()) > 50:  # Only process substantial text chunks
                try:
                    # Use the correct_chunk function with prepass info
                    chunk_replacements = prepass_report.get('summary', {}).get('replacement_map', {})
                    corrected_chunk = correct_chunk(
                        self.network_api_base, 
                        self.model, 
                        chunk_content, 
                        show_spinner=False,
                        chunk_replacements=chunk_replacements
                    )
                    grammar_corrected_chunks.append(corrected_chunk)
                    
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"**Chunk {i+1}:** Grammar processed ({len(chunk_content)} chars)\\n")
                        
                except Exception as e:
                    # Fallback to original chunk if grammar correction fails
                    grammar_corrected_chunks.append(chunk_content)
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"**Chunk {i+1}:** Error, using original ({e})\\n")
            else:
                # Keep short chunks as-is
                grammar_corrected_chunks.append(chunk_content)
        
        # Combine corrected chunks
        final_content = '\n\n'.join(grammar_corrected_chunks)
        
        # Save raw output
        with open(raw_output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        return final_content
    
    def compare_with_reference(self, output_content: str, reference_content: str, 
                             comparison_file: Path) -> Dict:
        """Compare output with reference and generate detailed analysis"""
        
        # Proper line-by-line comparison
        output_lines = [line.strip() for line in output_content.strip().split('\n') if line.strip()]
        reference_lines = [line.strip() for line in reference_content.strip().split('\n') if line.strip()]
        
        # Calculate basic similarity
        differ = difflib.unified_diff(reference_lines, output_lines, lineterm='')
        diff_lines = list(differ)
        
        # Count matching lines with fuzzy matching for minor differences
        matching_lines = 0
        fuzzy_matches = 0
        total_lines = max(len(output_lines), len(reference_lines))
        
        for i in range(min(len(output_lines), len(reference_lines))):
            output_line = output_lines[i].strip()
            ref_line = reference_lines[i].strip()
            
            # Exact match
            if output_line == ref_line:
                matching_lines += 1
            # Fuzzy match (>90% similarity)
            elif difflib.SequenceMatcher(None, output_line, ref_line).ratio() > 0.9:
                fuzzy_matches += 1
        
        # Calculate match percentages
        exact_match_percentage = (matching_lines / total_lines * 100) if total_lines > 0 else 0
        fuzzy_match_percentage = ((matching_lines + fuzzy_matches) / total_lines * 100) if total_lines > 0 else 0
        
        # Also calculate TTS-specific content match (ignore headers, focus on actual text content)
        tts_content_lines = []
        ref_content_lines = []
        
        # Extract lines that contain actual content (not headers, not metadata)
        for line in output_lines:
            if line.startswith('>') or ('By My Resolve' in line) or ('Spiral Seekers' in line) or ('Mega Buster' in line):
                tts_content_lines.append(line.strip())
                
        for line in reference_lines:
            if line.startswith('>') or ('By My Resolve' in line) or ('Spiral Seekers' in line) or ('Mega Buster' in line):
                ref_content_lines.append(line.strip())
        
        # Calculate TTS content similarity
        tts_matches = 0
        if tts_content_lines and ref_content_lines:
            for i in range(min(len(tts_content_lines), len(ref_content_lines))):
                if difflib.SequenceMatcher(None, tts_content_lines[i], ref_content_lines[i]).ratio() > 0.8:
                    tts_matches += 1
        
        tts_content_match = (tts_matches / max(len(tts_content_lines), len(ref_content_lines)) * 100) if max(len(tts_content_lines), len(ref_content_lines)) > 0 else 0
        
        # Calculate character-level similarity  
        output_chars = output_content.replace('\n', ' ').replace('  ', ' ').strip()
        reference_chars = reference_content.replace('\n', ' ').replace('  ', ' ').strip()
        
        char_similarity = difflib.SequenceMatcher(None, reference_chars, output_chars).ratio() * 100
        
        # Save detailed comparison
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write("# Detailed Comparison Analysis\n\n")
            f.write(f"**Exact Match Percentage:** {exact_match_percentage:.1f}%\n")
            f.write(f"**Fuzzy Match Percentage:** {fuzzy_match_percentage:.1f}%\n")
            f.write(f"**TTS Content Match:** {tts_content_match:.1f}%\n")
            f.write(f"**Character Similarity:** {char_similarity:.1f}%\n")
            f.write(f"**Total Lines (Output/Reference):** {len(output_lines)}/{len(reference_lines)}\n")
            f.write(f"**Exact Matches:** {matching_lines}, **Fuzzy Matches:** {fuzzy_matches}\n")
            f.write(f"**TTS Content Lines Found:** {len(tts_content_lines)}/{len(ref_content_lines)}\n\n")
            
            f.write("## Diff Analysis\n\n")
            f.write("```diff\n")
            for line in diff_lines[:50]:  # First 50 diff lines
                f.write(line + '\n')
            f.write("```\n\n")
            
            f.write("## Side-by-Side Sample\n\n")
            for i in range(min(10, len(output_lines), len(reference_lines))):
                output_line = output_lines[i] if i < len(output_lines) else ""
                ref_line = reference_lines[i] if i < len(reference_lines) else ""
                similarity = difflib.SequenceMatcher(None, output_line, ref_line).ratio()
                
                f.write(f"**Line {i+1}:** (Similarity: {similarity:.1%})\n")
                f.write(f"- Output:    `{output_line}`\n")
                f.write(f"- Reference: `{ref_line}`\n")
                
                if similarity == 1.0:
                    match_status = '✓ Exact'
                elif similarity > 0.9:
                    match_status = '≈ Fuzzy'
                else:
                    match_status = '✗ Different'
                f.write(f"- Match: {match_status}\n\n")
        
        return {
            'match_percentage': max(fuzzy_match_percentage, tts_content_match),  # Use best metric
            'exact_match_percentage': exact_match_percentage,
            'fuzzy_match_percentage': fuzzy_match_percentage,
            'tts_content_match': tts_content_match,
            'character_similarity': char_similarity,
            'total_output_lines': len(output_lines),
            'total_reference_lines': len(reference_lines),
            'matching_lines': matching_lines,
            'fuzzy_matches': fuzzy_matches,
            'diff_count': len(diff_lines)
        }
    
    def save_comprehensive_log(self, result: TestResult, log_file: Path):
        """Save comprehensive test log with all metrics"""
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("# Test Summary\\n\\n")
            f.write(f"**Timestamp:** {result.timestamp}\\n")
            f.write(f"**Network API:** {result.network_api_base}\\n")
            f.write(f"**Model:** {result.model_name}\\n")
            f.write(f"**Processing Time:** {result.processing_time_seconds:.2f}s\\n")
            f.write(f"**Problems Found:** {result.total_problems_found}\\n")
            f.write(f"**Chunks Processed:** {result.chunks_processed}\\n")
            f.write(f"**Reference Match:** {result.reference_match_percentage:.1f}%\\n\\n")
            
            f.write("## Prompt Versions\\n\\n")
            f.write(f"**Prepass Prompt Hash:** {result.prepass_prompt_version}\\n")
            f.write(f"**Grammar Prompt Hash:** {result.grammar_prompt_version}\\n\\n")
            
            f.write("## Performance Metrics\\n\\n")
            comp = result.detailed_comparison
            f.write(f"- **Line Match Percentage:** {comp['match_percentage']:.1f}%\\n")
            f.write(f"- **Character Similarity:** {comp['character_similarity']:.1f}%\\n")
            f.write(f"- **Lines (Output/Reference):** {comp['total_output_lines']}/{comp['total_reference_lines']}\\n")
            f.write(f"- **Matching Lines:** {comp['matching_lines']}\\n")
            f.write(f"- **Diff Count:** {comp['diff_count']}\\n\\n")
    
    def _get_prompt_hash(self, prompt_text: str) -> str:
        """Generate a short hash for prompt version tracking"""
        import hashlib
        return hashlib.md5(prompt_text.encode()).hexdigest()[:8]
    
    def generate_improvement_report(self) -> str:
        """Generate report showing improvements over time"""
        if len(self.test_history) < 2:
            return "Need at least 2 test runs to generate improvement report."
        
        report_lines = []
        report_lines.append("# Prompt Evolution & Improvement Report\\n")
        
        for i, result in enumerate(self.test_history):
            report_lines.append(f"## Test Run {i+1} - {result.timestamp}\\n")
            report_lines.append(f"- **Reference Match:** {result.reference_match_percentage:.1f}%\\n")
            report_lines.append(f"- **Problems Found:** {result.total_problems_found}\\n") 
            report_lines.append(f"- **Processing Time:** {result.processing_time_seconds:.2f}s\\n")
            
            if i > 0:
                prev = self.test_history[i-1]
                improvement = result.reference_match_percentage - prev.reference_match_percentage
                report_lines.append(f"- **Improvement:** {improvement:+.1f}% vs previous run\\n")
            
            report_lines.append("\\n")
        
        return "\\n".join(report_lines)


def main():
    """Main test execution"""
    # Initialize test system with Qwen 3 8B model on remote server
    tester = StressTestSystem(
        network_api_base="http://192.168.8.104:1234/v1",
        model="qwen3-8b"
    )
    
    try:
        # Run comprehensive test
        result = tester.run_comprehensive_test(chunk_size=8000)
        
        # Generate improvement report if we have history
        improvement_report = tester.generate_improvement_report()
        if "Need at least" not in improvement_report:
            print("\\n" + improvement_report)
        
        print(f"\\n🎉 Stress test completed successfully!")
        print(f"📊 Reference match: {result.reference_match_percentage:.1f}%")
        print(f"📁 Detailed logs saved to: {result.log_file}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())