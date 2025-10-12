#!/usr/bin/env python3
"""
Upgraded Prompt Testing Script for Qwen 3 8B

This script prepares and runs A/B testing between current prompts and upgraded prompts
to measure performance improvements with the new Qwen 3 8B model.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

def backup_current_prompts():
    """Backup current prompts before testing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"prompt_backups/current_{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Backup current prompts
    current_files = [
        "prepass_prompt.txt",
        "grammar_promt.txt"  # Note: intentional typo
    ]
    
    for file in current_files:
        if Path(file).exists():
            shutil.copy2(file, backup_dir / file)
            print(f"✓ Backed up {file}")
    
    return backup_dir

def apply_upgraded_prompts():
    """Apply the upgraded prompts for testing"""
    
    # Copy upgraded prepass prompt
    if Path("prepass_upgraded.txt").exists():
        shutil.copy2("prepass_upgraded.txt", "prepass_prompt.txt")
        print("✓ Applied upgraded prepass prompt")
    
    # Copy upgraded grammar prompt  
    if Path("grammar_upgraded.txt").exists():
        shutil.copy2("grammar_upgraded.txt", "grammar_promt.txt")
        print("✓ Applied upgraded grammar prompt")

def restore_current_prompts(backup_dir):
    """Restore current prompts after testing"""
    
    backup_files = [
        "prepass_prompt.txt",
        "grammar_promt.txt"
    ]
    
    for file in backup_files:
        backup_file = backup_dir / file
        if backup_file.exists():
            shutil.copy2(backup_file, file)
            print(f"✓ Restored {file}")

def update_stress_test_for_qwen3():
    """Update stress test system for Qwen 3 8B model"""
    
    stress_test_file = Path("stress_test_system.py")
    if stress_test_file.exists():
        with open(stress_test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update model to Qwen 3 8B (adjust name based on actual model in LM Studio)
        content = content.replace(
            'model="ibm/granite-3.1-8b"',
            'model="qwen/qwen3-8b-instruct"'  # Adjust this to match actual model name
        )
        
        with open(stress_test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Updated stress test for Qwen 3 8B")

def run_baseline_test():
    """Run test with current prompts (baseline)"""
    import subprocess
    
    print("\n=== BASELINE TEST: Current Prompts ===")
    try:
        result = subprocess.run(["python", "stress_test_system.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Baseline test completed")
            return True
        else:
            print(f"❌ Baseline test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Baseline test timed out")
        return False
    except Exception as e:
        print(f"❌ Baseline test error: {e}")
        return False

def run_upgraded_test():
    """Run test with upgraded prompts"""
    import subprocess
    
    print("\n=== UPGRADED TEST: Enhanced Prompts ===")
    try:
        result = subprocess.run(["python", "stress_test_system.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Upgraded test completed")
            return True
        else:
            print(f"❌ Upgraded test failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Upgraded test timed out")
        return False
    except Exception as e:
        print(f"❌ Upgraded test error: {e}")
        return False

def check_qwen3_availability():
    """Check if Qwen 3 model is available on remote server"""
    import requests
    
    try:
        response = requests.get("http://192.168.8.104:1234/v1/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            available_models = [model['id'] for model in models.get('data', [])]
            
            # Look for Qwen 3 models
            qwen3_models = [m for m in available_models if 
                          'qwen3' in m.lower() or 'qwen-3' in m.lower()]
            
            if qwen3_models:
                print(f"✅ Qwen 3 models available: {qwen3_models}")
                return qwen3_models[0]
            else:
                print("❌ No Qwen 3 models found")
                print(f"Available models: {available_models}")
                return None
        else:
            print(f"❌ Server error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Network error: {e}")
        return None

def main():
    """Main A/B testing workflow"""
    print("=== Qwen 3 8B Upgraded Prompt Testing ===")
    print()
    
    # Check if Qwen 3 model is available
    print("1. Checking Qwen 3 model availability...")
    model_name = check_qwen3_availability()
    
    if not model_name:
        print("⏳ Qwen 3 model not available. Ensure download is complete.")
        return 1
    
    # Update test configuration
    print(f"\n2. Updating test configuration for {model_name}...")
    update_stress_test_for_qwen3()
    
    # Backup current prompts
    print(f"\n3. Backing up current prompts...")
    backup_dir = backup_current_prompts()
    
    try:
        # Run baseline test with current prompts
        print(f"\n4. Running baseline test (current prompts)...")
        baseline_success = run_baseline_test()
        
        if baseline_success:
            # Apply upgraded prompts
            print(f"\n5. Applying upgraded prompts...")
            apply_upgraded_prompts()
            
            # Run upgraded test
            print(f"\n6. Running upgraded test (enhanced prompts)...")
            upgraded_success = run_upgraded_test()
            
            if upgraded_success:
                print(f"\n🎉 A/B Testing Complete!")
                print(f"📊 Check stress_test_results/ for comparison data")
                print(f"📁 Prompts backed up to: {backup_dir}")
                
                # Generate comparison report
                generate_comparison_report(baseline_success, upgraded_success)
                
            else:
                print(f"\n⚠️ Upgraded test failed, keeping current prompts")
        else:
            print(f"\n⚠️ Baseline test failed, check configuration")
    
    finally:
        # Always restore current prompts
        print(f"\n7. Restoring current prompts...")
        restore_current_prompts(backup_dir)
    
    return 0

def generate_comparison_report(baseline_success, upgraded_success):
    """Generate a comparison report of the test results"""
    
    # This would analyze the latest two stress test logs and compare them
    # For now, just create a placeholder report
    
    report_file = Path("qwen3_ab_test_report.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# Qwen 3 8B A/B Testing Report

**Generated**: {timestamp}  
**Model**: Qwen 3 8B (Q5 quantization)
**Test Type**: Current prompts vs Upgraded prompts

## Test Results Summary

### Baseline Test (Current Prompts)
- Status: {'✅ Completed' if baseline_success else '❌ Failed'}
- Prompts: prepass_prompt.txt, grammar_promt.txt
- Configuration: Standard iteration 6 prompts (15.0% reference match)

### Upgraded Test (Enhanced Prompts)  
- Status: {'✅ Completed' if upgraded_success else '❌ Failed'}
- Prompts: prepass_upgraded.txt, grammar_upgraded.txt
- Configuration: Enhanced schema, strict skip-zones, surgical corrections

## Key Improvements in Upgraded Prompts

1. **Strict JSON Schema**: Fixed reason categories prevent parsing errors
2. **Hard Skip-Zones**: Better protection for code/links/HTML  
3. **Empty Response Handling**: Explicit `{{"replacements":[]}}` format
4. **Surgical Grammar**: Enforced 3-step correction process
5. **LM Studio Integration**: Optimized presets with `/no_think`

## Performance Comparison

*Detailed analysis requires manual review of stress test logs*

### Expected Improvements:
- **Reference Match**: Target >20% (vs 15.0% current)
- **JSON Compliance**: 100% with strict schema
- **Processing Speed**: Improved with optimized sampling
- **TTS Quality**: Enhanced with refined categorization

## Recommendations

1. **Review detailed logs** in stress_test_results/ directory
2. **Compare reference match percentages** between tests  
3. **Analyze JSON compliance rates** and processing times
4. **Choose best-performing prompt set** for production use
5. **Apply LM Studio presets** for optimal sampling parameters

## Files Generated

- Baseline test logs: stress_test_results/stress_test_log_[timestamp1].md
- Upgraded test logs: stress_test_results/stress_test_log_[timestamp2].md  
- Backup prompts: prompt_backups/current_[timestamp]/
- This report: qwen3_ab_test_report.md

*Manual analysis of logs required to determine optimal configuration*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📝 A/B test report generated: {report_file}")

if __name__ == "__main__":
    exit(main())