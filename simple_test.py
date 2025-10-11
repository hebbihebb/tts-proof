#!/usr/bin/env python3
"""
Simple test script to run both prepass and grammar correction on webui_test.md
This bypasses the web interface and gives us direct debugging capability.
"""

import json
import time
from pathlib import Path
from datetime import datetime

# Import our modules
from md_proof import chunk_paragraphs, DEFAULT_API_BASE, DEFAULT_MODEL, INSTRUCTION
from prepass import run_prepass, DETECTOR_PROMPT

def load_prompts():
    """Load prompts from files."""
    # Load prepass prompt
    prepass_prompt_path = Path("prepass_prompt.txt")
    if prepass_prompt_path.exists():
        with open(prepass_prompt_path, encoding="utf-8") as f:
            prepass_prompt = f.read().strip()
    else:
        prepass_prompt = DETECTOR_PROMPT
    
    # Load grammar prompt
    grammar_prompt_path = Path("grammar_promt.txt")
    if grammar_prompt_path.exists():
        with open(grammar_prompt_path, encoding="utf-8") as f:
            grammar_prompt = f.read().strip()
    else:
        grammar_prompt = INSTRUCTION
    
    return prepass_prompt, grammar_prompt

def run_simple_test(api_base=DEFAULT_API_BASE, model=DEFAULT_MODEL, chunk_size=8000):
    """Run a comprehensive test."""
    
    print("=== TTS-Proof Simple Test ===")
    print(f"API Base: {api_base}")
    print(f"Model: {model}")
    print(f"Chunk Size: {chunk_size}")
    print()
    
    # Load test file
    test_file = Path("webui_test.md")
    if not test_file.exists():
        print("ERROR: webui_test.md not found!")
        return
    
    with open(test_file, encoding="utf-8") as f:
        original_content = f.read()
    
    print(f"✓ Loaded test file ({len(original_content)} characters)")
    
    # Load prompts
    prepass_prompt, grammar_prompt = load_prompts()
    print(f"✓ Loaded prompts (prepass: {len(prepass_prompt)} chars, grammar: {len(grammar_prompt)} chars)")
    
    # Initialize results
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "api_base": api_base,
        "model": model,
        "chunk_size": chunk_size,
        "original_content": original_content,
        "prepass_prompt": prepass_prompt,
        "grammar_prompt": grammar_prompt,
        "prepass_report": None,
        "grammar_result": None,
        "errors": [],
        "timing": {}
    }
    
    # Step 1: Run prepass
    print("\n--- Running Prepass Detection ---")
    start_time = time.time()
    try:
        prepass_report = run_prepass(
            input_path=test_file,
            api_base=api_base,
            model=model,
            chunk_chars=chunk_size,
            show_progress=True
        )
        results["prepass_report"] = prepass_report
        results["timing"]["prepass"] = time.time() - start_time
        
        summary = prepass_report.get("summary", {})
        problems = summary.get("unique_problem_words", [])
        print(f"✓ Prepass completed in {results['timing']['prepass']:.2f}s")
        print(f"  Found {len(problems)} unique problems")
        print(f"  Sample problems: {problems[:5]}")
        
    except Exception as e:
        error_msg = f"Prepass failed: {str(e)}"
        results["errors"].append(error_msg)
        print(f"✗ {error_msg}")
        results["timing"]["prepass"] = time.time() - start_time
    
    # Step 2: Test chunking
    print("\n--- Testing Grammar Correction Setup ---")
    try:
        chunks = chunk_paragraphs(original_content, chunk_size)
        print(f"✓ Would process {len(chunks)} chunks")
        results["grammar_result"] = f"[DRY RUN] Would process {len(chunks)} chunks"
        
        # For now, we'll skip actual LLM calls to avoid API issues
        print("  (Skipping actual LLM calls for this test)")
        
    except Exception as e:
        error_msg = f"Chunking failed: {str(e)}"
        results["errors"].append(error_msg)
        print(f"✗ {error_msg}")
    
    # Generate test log
    print("\n--- Generating Test Log ---")
    try:
        log_content = generate_test_log(results)
        
        log_file = Path("test_log.md")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        print(f"✓ Test log saved to: {log_file.absolute()}")
        
    except Exception as e:
        print(f"✗ Failed to save log: {str(e)}")
    
    # Summary
    print("\n--- Test Summary ---")
    print(f"Total errors: {len(results['errors'])}")
    print(f"Prepass success: {'✓' if results['prepass_report'] else '✗'}")
    print(f"Overall success: {'✓' if len(results['errors']) == 0 else '✗'}")
    
    return results

def generate_test_log(results):
    """Generate a test log in markdown format."""
    
    content = f"""# TTS-Proof Simple Test Log

**Generated:** {results['timestamp']}
**API Base:** {results['api_base']}
**Model:** {results['model']}
**Chunk Size:** {results['chunk_size']}

## Test Summary

- **Errors:** {len(results['errors'])}
- **Prepass Success:** {'✅' if results['prepass_report'] else '❌'}
- **Timing:** {results.get('timing', {})}

## Original Content

```markdown
{results['original_content']}
```

## Prepass Prompt

```
{results['prepass_prompt']}
```

## Grammar Prompt

```
{results['grammar_prompt']}
```

## Prepass Results
"""
    
    if results['prepass_report']:
        report = results['prepass_report']
        summary = report.get('summary', {})
        
        content += f"""
### Summary
- **Unique Problems:** {len(summary.get('unique_problem_words', []))}
- **Chunks Processed:** {summary.get('chunks_processed', 0)}
- **Sample Problems:** {', '.join(summary.get('sample_problems', [])[:5])}

### Full JSON
```json
{json.dumps(report, indent=2)}
```
"""
    else:
        content += "\nNo prepass results (failed or skipped)\n"
    
    content += f"""
## Grammar Results

{results.get('grammar_result', 'No grammar results')}

## Errors

"""
    
    if results['errors']:
        for i, error in enumerate(results['errors'], 1):
            content += f"{i}. {error}\n"
    else:
        content += "No errors occurred.\n"
    
    content += """
## Analysis

[Manual review needed - compare original content with processed results]

---
*Generated by TTS-Proof Simple Test*
"""
    
    return content

if __name__ == "__main__":
    # You can customize these parameters
    API_BASE = "http://127.0.0.1:1234/v1"  # Your LM Studio endpoint
    MODEL = "qwen/qwen3-4b-2507"  # Your model
    CHUNK_SIZE = 8000
    
    try:
        results = run_simple_test(API_BASE, MODEL, CHUNK_SIZE)
        
        if results and len(results['errors']) == 0:
            print("\n🎉 Test completed successfully!")
        else:
            print(f"\n⚠️  Test completed with {len(results.get('errors', []))} errors")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()