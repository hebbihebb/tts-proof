#!/usr/bin/env python3
"""Test the line-based detector response parser."""

text = """FIND: Bʏ Mʏ Rᴇsᴏʟᴠᴇ!
REPLACE: By My Resolve!
REASON: small caps
---
FIND: *BANG!*
REPLACE: bang
REASON: asterisk sound
---
END_REPLACEMENTS"""

replacements = []
current = {}

lines = text.split('\n')
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

print(f'✅ Parsed {len(replacements)} replacements:')
for r in replacements:
    print(f"  {r['find'][:40]} → {r['replace'][:40]}")
    print(f"    Reason: {r['reason']}")
