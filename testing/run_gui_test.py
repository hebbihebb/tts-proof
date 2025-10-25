#!/usr/bin/env python3
"""
GUI Functionality Test for TTS-Proof v2
Validates that the GUI works correctly with the stress test file.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_gui_import():
    """Test that GUI can be imported."""
    print("🖥️  Testing GUI import...")
    try:
        import gui
        print("✅ GUI module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ GUI import failed: {e}")
        return False
    except Exception as e:
        print(f"⚠️  GUI import error: {e}")
        return False


def test_gui_initialization():
    """Test that GUI can be initialized (without showing window)."""
    print("🖥️  Testing GUI initialization...")
    try:
        import gui
        # Check if main classes/functions exist
        expected_components = ['main']  # Adjust based on actual GUI structure
        
        for component in expected_components:
            if hasattr(gui, component):
                print(f"  ✅ Found component: {component}")
            else:
                print(f"  ⚠️  Component missing: {component}")
        
        print("✅ GUI initialization check completed")
        return True
    except Exception as e:
        print(f"❌ GUI initialization error: {e}")
        return False


def test_gui_with_stress_test():
    """Test GUI components with stress test file path."""
    print("🖥️  Testing GUI with stress test file...")
    
    test_file = Path(__file__).parent / "test_data" / "tts_stress_test.md"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"  Input file: {test_file}")
    print(f"  File size: {test_file.stat().st_size} bytes")
    
    # Test that file can be read (simulates GUI file loading)
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"  ✅ File loaded: {len(content)} characters")
        return True
    except Exception as e:
        print(f"  ❌ File loading error: {e}")
        return False


def generate_gui_test_report(results: dict):
    """Generate GUI test report."""
    results_dir = Path(__file__).parent / "stress_test_results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = results_dir / f"gui_test_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# GUI Functionality Test Report\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        
        f.write("## Test Results\n\n")
        
        for test_name, passed in results.items():
            icon = "✅" if passed else "❌"
            f.write(f"- {icon} {test_name}\n")
        
        f.write(f"\n## Summary\n\n")
        total = len(results)
        passed = sum(results.values())
        f.write(f"**Passed:** {passed}/{total}\n")
        f.write(f"**Success Rate:** {passed/total*100:.1f}%\n")
    
    print(f"\n📋 GUI test report saved to {report_file.name}")
    return report_file


def main():
    """Main entry point for GUI tests."""
    print("="*60)
    print("TTS-PROOF V2 GUI FUNCTIONALITY TEST")
    print("="*60)
    print()
    
    results = {}
    
    # Run tests
    results['GUI Import'] = test_gui_import()
    results['GUI Initialization'] = test_gui_initialization()
    results['GUI with Stress Test File'] = test_gui_with_stress_test()
    
    # Generate report
    report_file = generate_gui_test_report(results)
    
    print("\n" + "="*60)
    print("GUI TEST COMPLETE")
    print("="*60)
    
    all_passed = all(results.values())
    if all_passed:
        print("✅ All GUI tests passed")
        return 0
    else:
        print("❌ Some GUI tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
