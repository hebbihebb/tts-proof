#!/usr/bin/env python3
"""
Round 2: Focused prompt optimization based on Round 1 results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_optimizer import PromptOptimizer, PROMPT_VARIATIONS

# Round 2 variations - building on Comprehensive TTS v2 success
PROMPT_VARIATIONS_R2 = [
    (
        "Best from R1 (baseline)",
        """Detect TTS-problematic patterns in Markdown. Fix patterns that would sound unnatural when read aloud.

TARGET PATTERNS:
• Stylized Unicode → Standard letters ("Bʏ" → "By", "Rᴇsᴏʟᴠᴇ" → "Resolve")
• Chat log brackets → Plain format ("[Username]:" → "Username:")
• All-caps words → Lowercase (unless proper noun) ("BANG" → "bang", "NO WAY" → "no way")
• Letter-spaced text → Normal spacing ("[M e g a]" → "[Mega]")
• Excessive punctuation → Single ("!!!" → "!", "???" → "?", "!?!?" → "?")
• Repeated emphasis → Single ("ugh ugh ugh" → "ugh")

SKIP:
✓ Code blocks (```) and inline code (`)
✓ Proper nouns and acronyms (NASA, API)
✓ Markdown syntax
✓ Normal punctuation
✓ Standard ellipsis (...)

Output format:
{"replacements": [{"find": "exact original text", "replace": "corrected text", "reason": "brief reason"}]}

Be aggressive - fix all TTS issues you find.

/no_think"""
    ),
    (
        "Enhanced Brackets + Caps",
        """Detect TTS-problematic patterns. Fix text that sounds bad when read aloud.

FIX THESE:
1. Stylized Unicode: "Bʏ" → "By", "Sᴘɪʀᴀʟ" → "Spiral", "Hᴏɴᴏʀɪɴɢ" → "Honoring"
2. Chat brackets: "[Username]:" → "Username:" (remove brackets around usernames)
3. ALL-CAPS emphasis: "NO WAY" → "no way", "BANG" → "bang", "AAAAAAA" → "aaa", "WHAT" → "what"
4. Letter spacing: "[M e g a]" → "[Mega]"
5. Excessive punct: "!!!" → "!", "!?!?!?" → "?", "???" → "?"
6. Repeated words: "bluh... Bluh... BLUH!" → "bluh"

PRESERVE:
- Code blocks and inline code
- Acronyms: NASA, API, GPU, CPU, RAM, USB, HTTP
- Markdown structure
- Single punctuation
- Ellipsis ...

JSON format:
{"replacements": [{"find": "exact text", "replace": "fixed", "reason": "type"}]}

Fix EVERY instance. Be thorough.

/no_think"""
    ),
    (
        "Caps Priority",
        """TTS normalizer - Fix text for speech synthesis.

HIGH PRIORITY FIXES:
• All-caps words → lowercase: "NO WAY" → "no way", "BANG" → "bang", "WHAT" → "what", "AAAAAAA" → "aaa"
• Stylized Unicode → ASCII: "Bʏ" → "By", "Rᴇsᴏʟᴠᴇ" → "Resolve", "Hᴏɴᴏʀɪɴɢ" → "Honoring"
• Chat brackets → remove: "[Username]:" → "Username:"
• Excessive punct → single: "!!!" → "!", "!?!?" → "?", "???" → "?"
• Letter-spaced → normal: "[M e g a]" → "[Mega]"
• Repeated emphasis → once: "bluh... Bluh... BLUH!" → "bluh"

EXCEPTIONS (don't change):
- NASA, API, GPU, CPU, RAM, USB, HTTP, HTTPS, URL, TTS, JSON, XML
- Code blocks (```)
- Inline code (`)
- Proper nouns at sentence start
- Markdown links/images

Output JSON only:
{"replacements": [{"find": "exact match from input", "replace": "corrected version", "reason": "pattern name"}]}

Find ALL matches. Maximum corrections.

/no_think"""
    ),
    (
        "Onomatopoeia Focus",
        """TTS detector - Normalize sound effects and emphasis for speech synthesis.

TARGET PATTERNS:
1. Stylized letters: "Bʏ" → "By", "Rᴇsᴏʟᴠᴇ" → "Resolve"
2. Sound effects: "*BANG!*" → "*bang*", "BLUH!" → "bluh"
3. Repeated sounds: "bluh... Bluh... BLUH!" → "bluh"
4. Laughs: "Aaahahaha" → "haha", "ahahaha" → "haha"
5. Screams: "AAAAAAA" → "aaa"
6. All-caps: "NO WAY" → "no way", "WHAT" → "what"
7. Chat brackets: "[User]:" → "User:"
8. Excessive punct: "!!!" → "!", "!?!?" → "?"
9. Letter spacing: "[M e g a]" → "[Mega]"

KEEP:
- Code blocks
- Acronyms
- Single punctuation
- Ellipsis

Format:
{"replacements": [{"find": "exact text", "replace": "fixed", "reason": "type"}]}

Aggressive corrections.

/no_think"""
    ),
    (
        "Simple + Exhaustive",
        """Fix TTS problems. Make text natural for speech synthesis.

CORRECTIONS:
• Fancy letters → normal: Any stylized Unicode → plain ASCII
• [Brackets]: Remove around usernames
• ALL CAPS → lowercase (except acronyms)
• Multiple punct → single: "!!!" → "!", "???" → "?"
• Repeated text → once: "ugh ugh ugh" → "ugh"
• Letter-spaced → joined: "[M e g a]" → "[Mega]"

Keep these:
- Code (``` or `)
- NASA API GPU CPU RAM USB HTTP HTTPS URL TTS
- Markdown structure
- Single ! ? .
- ... ellipsis

Output:
{"replacements": [{"find": "exact original", "replace": "fixed version", "reason": "type"}]}

Fix everything. Be exhaustive.

/no_think"""
    ),
    (
        "Minimal Instructions",
        """Fix text for TTS. Find ALL instances of these patterns and normalize them:

Stylized Unicode → ASCII
[Username]: → Username:
ALL-CAPS → lowercase (keep NASA, API, GPU, CPU, RAM, USB, HTTP)
!!! → !
!?!? → ?
Letter-spaced → normal
Repeated words → single

Skip: code blocks, inline code, markdown, ellipsis

{"replacements": [{"find": "exact", "replace": "fixed", "reason": "type"}]}

/no_think"""
    )
]


def main():
    """Run Round 2 optimization."""
    test_dir = Path(__file__).parent
    optimizer = PromptOptimizer(test_dir)
    print("\n🔬 ROUND 2: Focused Optimization")
    print("   Building on Comprehensive TTS v2 (53.37% baseline)\n")
    optimizer.run_optimization(PROMPT_VARIATIONS_R2)


if __name__ == "__main__":
    main()
