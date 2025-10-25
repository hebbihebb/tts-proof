#!/usr/bin/env python3
"""Quick test of chunked detector with line-based format."""

import sys
sys.path.insert(0, '.')

from md_processor import LLMClient, PROMPTS, mask_protected

# Load test text
with open('testing/test_data/tts_stress_test.md', encoding='utf-8') as f:
    text = f.read()

print(f"📄 Loaded {len(text)} chars")

# Mask it
masked, mask_table = mask_protected(text)
print(f"🔒 Masked to {len(masked)} chars ({len(mask_table)} masks)")

# Chunk it
chunk_size = 600
chunks = []
for i in range(0, len(masked), chunk_size):
    chunk = masked[i:i + chunk_size]
    if chunk.strip():
        chunks.append(chunk)

print(f"✂️  Split into {len(chunks)} chunks")

# Test with first chunk only
llm = LLMClient('http://127.0.0.1:1234/v1', 'qwen/qwen3-4b-2507')

print(f"\n🧪 Testing chunk 1 (first {len(chunks[0])} chars)...")
print(f"Preview: {chunks[0][:100]}...\n")

detector_prompt = PROMPTS.get('detector', 'Find problems')
response = llm.complete(detector_prompt, chunks[0], temperature=0.3, repetition_penalty=1.5, max_tokens=1024)

print("📥 LLM Response:")
print("=" * 60)
print(response[:500])
print("=" * 60)

# Parse it
replacements = []
current = {}
lines = response.split('\n')
for line in lines:
    line = line.strip()
    if not line or line == '---':
        if 'find' in current and 'replace' in current:
            replacements.append(current)
        current = {}
        continue
    if line == 'END_REPLACEMENTS':
        break
    if line.startswith('FIND:'):
        current['find'] = line[5:].strip()
    elif line.startswith('REPLACE:'):
        current['replace'] = line[8:].strip()
    elif line.startswith('REASON:'):
        current['reason'] = line[7:].strip()

print(f"\n✅ Parsed {len(replacements)} replacements:")
for i, r in enumerate(replacements, 1):  # Show all
    find_preview = r['find'][:50].replace('\n', ' ')
    replace_preview = r['replace'][:50].replace('\n', ' ')
    print(f"{i}. \"{find_preview}\" → \"{replace_preview}\"")
    print(f"   Reason: {r['reason']}")
