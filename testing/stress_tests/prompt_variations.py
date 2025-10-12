"""
Prompt Variations for Testing

Different prepass prompt variations to test for improved accuracy.
Each variation focuses on different aspects of TTS problem detection.
"""

# Variation 1: Current optimized prompt
PROMPT_V1_CURRENT = """Find stylized Unicode letters and normalize to standard English. Return JSON only.

Examples:
"Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!"  
"Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!" → "Spiral Seekers!"
"[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip: normal text, usernames, punctuation, code.

Format:
{"replacements": [{"find": "text", "replace": "fixed", "reason": "unicode"}]}"""

# Variation 2: More detailed with specific Unicode types
PROMPT_V2_DETAILED = """Detect and fix TTS problems caused by stylized Unicode characters. Return JSON only.

**Unicode Types to Fix:**
- Small caps: ʟ ᴀ ᴇ ʀ ɪ ᴏ ᴜ ʏ ɴ ᴛ s ᴄ ᴅ ғ ɢ ʜ ᴊ ᴋ ᴍ ᴘ ǫ ᴠ ᴡ ᴢ
- Fullwidth: ０１２３４５６７８９ＡＢＣＤＥＦ
- Combining diacritics: é ñ ü (when stylized)
- Zero-width spaces and joiners

**Examples:**
"Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!"
"Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!" → "Spiral Seekers!"
"[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

**Skip:**
- Normal punctuation and emphasis (!!!, ???, ...)
- Usernames and chat tags ([Username])
- Code blocks and technical text
- Natural ellipses and stuttering
- Valid foreign language text

**Format:**
{"replacements": [{"find": "text", "replace": "fixed", "reason": "unicode"}]}"""

# Variation 3: Ultra-concise with clear directives
PROMPT_V3_CONCISE = """Fix Unicode small caps and stylized letters. JSON only.

Examples:
Bʏ Mʏ Rᴇsᴏʟᴠᴇ! → By My Resolve!
Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs! → Spiral Seekers!
[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ] → [Mega Buster]

Skip usernames, normal text, code, punctuation.

Format: {"replacements": [{"find": "...", "replace": "...", "reason": "unicode"}]}"""

# Variation 4: Step-by-step instruction format
PROMPT_V4_STEPBYSTEP = """You are a TTS problem detector. Follow these steps:

1. **Scan** for Unicode small caps (ʟ ᴀ ᴇ ʀ ɪ ᴏ ᴜ ʏ, etc.)
2. **Identify** words with stylized letters
3. **Convert** to normal ASCII letters
4. **Skip** normal text, usernames, punctuation, code

Examples:
- "Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!" (reason: unicode)
- "Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!" → "Spiral Seekers!" (reason: unicode)
- "BANG!" → "BANG!" (reason: skip - normal emphasis)

Return JSON: {"replacements": [{"find": "text", "replace": "fixed", "reason": "unicode"}]}"""

# Variation 5: Focus on precision with negative examples
PROMPT_V5_PRECISION = """Detect ONLY stylized Unicode small caps and convert to normal text. Return JSON.

✅ **Fix These:**
Bʏ Mʏ Rᴇsᴏʟᴠᴇ! → By My Resolve!
Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs! → Spiral Seekers!
[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ] → [Mega Buster]

❌ **Skip These:**
BANG! (normal caps)
AAAAAAA (onomatopoeia)
[Username] (chat tags)
... (ellipses)
Je ne sais pas (foreign text)
Dr. Brown at 5 p.m. (abbreviations)

Format: {"replacements": [{"find": "original", "replace": "fixed", "reason": "unicode"}]}"""

# Variation 6: Emphasize context preservation
PROMPT_V6_CONTEXT = """Find and normalize Unicode small caps while preserving context.

**Target:** Small cap Unicode (ʟ ᴀ ᴇ ʀ ɪ ᴏ ᴜ ʏ ɴ ᴛ s ᴄ ᴅ ғ ɢ ʜ ᴊ ᴋ ᴍ ᴘ ǫ ᴠ ᴡ ᴢ)

**Examples:**
"Bʏ Mʏ Rᴇsᴏʟᴠᴇ!" → "By My Resolve!" (normalize small caps, keep !)
"Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!" → "Spiral Seekers!" (normalize small caps, keep !)

**Preserve:**
- Markdown formatting (**, *, `, etc.)
- Punctuation patterns (!!, ..., ---)
- Chat usernames and tags
- Code and technical text
- Natural speech patterns

JSON: {"replacements": [{"find": "exact text", "replace": "fixed text", "reason": "unicode"}]}"""

PROMPT_VARIATIONS = {
    "v1_current": PROMPT_V1_CURRENT,
    "v2_detailed": PROMPT_V2_DETAILED,
    "v3_concise": PROMPT_V3_CONCISE,
    "v4_stepbystep": PROMPT_V4_STEPBYSTEP,
    "v5_precision": PROMPT_V5_PRECISION,
    "v6_context": PROMPT_V6_CONTEXT,
}
