#!/usr/bin/env python3
"""
Test the improved sentinel handling.
"""

from md_proof import extract_between_sentinels, SENTINEL_START, SENTINEL_END

def test_sentinel_extraction():
    print("Testing improved sentinel extraction...")
    
    # Test cases
    test_cases = [
        # Normal case
        f"{SENTINEL_START}\nClean text\n{SENTINEL_END}",
        # LLM included sentinel in response
        f"{SENTINEL_START}\nText with {SENTINEL_END} in middle\n{SENTINEL_END}",
        # No sentinels but stray sentinel at end
        f"Text without sentinels{SENTINEL_END}",
        # Just the text
        "Plain text without any sentinels",
    ]
    
    expected = [
        "Clean text",
        "Text with  in middle",
        "Text without sentinels",
        "Plain text without any sentinels"
    ]
    
    for i, (test_input, expected_output) in enumerate(zip(test_cases, expected)):
        result = extract_between_sentinels(test_input)
        print(f"Test {i+1}: {'✓' if result == expected_output else '✗'}")
        print(f"  Input: {repr(test_input)}")
        print(f"  Expected: {repr(expected_output)}")
        print(f"  Got: {repr(result)}")
        print()

if __name__ == '__main__':
    test_sentinel_extraction()