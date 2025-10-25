#!/usr/bin/env python3
"""
Master Test Runner for TTS-Proof v2 Stress Testing
Orchestrates all tests: pipeline, GUI, and comparison with reference.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_test_script(script_name: str, description: str, extra_args: list = None):
    """Run a test script and capture results."""
    print("\n" + "="*60)
    print(f"Running: {description}")
    print("="*60)
    
    script_path = Path(__file__).parent / script_name
    
    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        success = result.returncode == 0
        return success
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False


def main():
    """Main orchestration of all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='TTS-Proof v2 Master Test Suite')
    parser.add_argument('--llm', action='store_true',
                        help='Include LLM phases in pipeline tests (requires LM Studio)')
    args = parser.parse_args()
    
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "TTS-PROOF V2 MASTER TEST SUITE" + " "*13 + "║")
    print("║" + " "*10 + "Stress Testing - feat/stress-test-validation" + " "*4 + "║")
    if args.llm:
        print("║" + " "*18 + "MODE: Full Pipeline + LLM" + " "*15 + "║")
    else:
        print("║" + " "*18 + "MODE: Prepass Only" + " "*19 + "║")
    print("╚" + "═"*58 + "╝")
    print()
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test 1: Core Pipeline Stress Test
    extra_args = ['--llm'] if args.llm else []
    results['Pipeline Stress Test'] = run_test_script(
        'run_stress_test.py',
        'Core Pipeline Stress Test' + (' (with LLM)' if args.llm else ' (prepass only)'),
        extra_args=extra_args
    )
    
    # Test 2: GUI Functionality Test
    results['GUI Functionality Test'] = run_test_script(
        'run_gui_test.py',
        'GUI Functionality Test'
    )
    
    # Summary
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " "*20 + "FINAL TEST SUMMARY" + " "*20 + "║")
    print("╚" + "═"*58 + "╝")
    print()
    
    for test_name, passed in results.items():
        icon = "✅" if passed else "❌"
        status = "PASSED" if passed else "FAILED"
        print(f"{icon} {test_name}: {status}")
    
    print()
    total = len(results)
    passed = sum(results.values())
    print(f"Total: {passed}/{total} test suites passed ({passed/total*100:.0f}%)")
    print()
    
    results_dir = Path(__file__).parent / "stress_test_results"
    print(f"📁 All results saved to: {results_dir}")
    print()
    
    if all(results.values()):
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Review reports for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
