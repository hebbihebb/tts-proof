# TTS-Proof Simple Test Log

**Generated:** 2025-10-11 19:32:38
**API Base:** http://127.0.0.1:1234/v1
**Model:** qwen/qwen3-4b-2507
**Chunk Size:** 8000

## Test Summary

- **Errors:** 0
- **Prepass Success:** ✅
- **Timing:** {'prepass': 24.140218496322632}

## Original Content

```markdown
# TTS Prepass Test Document

This document contains various patterns that are problematic for text-to-speech engines.

## Spaced and Stylized Letters

The F ʟ ᴀ s ʜ D ᴀ ɴ ᴄ ᴇ technique is very effective.

Some T E S T content with spacing issues.

The [M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ] weapon is powerful.

## Weird Capitalization

This REALLY LONG CAPITALIZED TITLE needs normalization.

ANOTHER_WEIRD_CAPS_THING should be fixed.

NASA and GPU are valid acronyms, but STRANGE_ACRONYM_EXAMPLE is not.

## Hyphenated Letter Sequences

The U-N-I-T-E-D States of America.

Some S-P-A-C-E-D words here.

## Mixed Problems

More F ʟ ᴀ s ʜ content to test deduplication.

The Q ᴜ ɪ ᴄ ᴋ brown fox jumps.

Some CAPS_LOCK_TEXT and more issues.

## Normal Text

This paragraph should not trigger any TTS problems. It contains normal text with proper capitalization, standard punctuation, and regular word spacing. This serves as a control to ensure the prepass detector only flags actual problems.

The code blocks should also be ignored:

```javascript
const CAPS_IN_CODE = "should be ignored";
const spaced_variable = F_L_A_S_H_DANCE;
```

And inline code like `CAPS_CODE` should be preserved.
```

## Prepass Prompt

```
You are a TTS preprocessing detector working with English text. Find problematic patterns and suggest specific English replacements.

Analyze the text and return JSON with problem words AND their recommended TTS-friendly English replacements:
- Stylized/spaced letters: "F ʟ ᴀ s ʜ" → "Flash"
- Hyphenated letters: "U-N-I-T-E-D" → "United"
- ALL-CAPS titles: "REALLY LONG TITLE" → "Really Long Title"
- Underscore caps: "WEIRD_CAPS_THING" → "Weird Caps Thing"
- Bracket stylized: "[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip valid acronyms (NASA, GPU, API, etc.) and preserve code blocks.

IMPORTANT: All replacements must be in standard English. Do not add accents or non-English characters.

Return JSON only:
{ "replacements": [ { "find": "<exact_text>", "replace": "<tts_friendly_version>", "reason": "<why>" } ] }
```

## Grammar Prompt

```
You are a grammar and spelling corrector for Markdown text.

CRITICAL: When prepass replacements are provided, apply them EXACTLY as specified. Do not modify or interpret them.

Primary focus:
1) Apply prepass TTS corrections precisely as given
2) Fix grammar, spelling, and punctuation errors
3) Improve sentence flow and readability

Preservation rules:
- Never edit Markdown syntax, code blocks, inline code, links/URLs, images, or HTML tags
- Keep all Markdown structure exactly as-is
- Preserve meaning and tone
- Keep valid acronyms (NASA, GPU, API, etc.)

Output only the corrected Markdown; no explanations.
```

## Prepass Results

### Summary
- **Unique Problems:** 10
- **Chunks Processed:** 0
- **Sample Problems:** 

### Full JSON
```json
{
  "source": "webui_test.md",
  "created_at": "2025-10-11T19:33:02.535900",
  "chunks": [
    {
      "id": 1,
      "range": {
        "start_byte": 0,
        "end_byte": 1050
      },
      "replacements": [
        {
          "find": "F \u029f \u1d00 s \u029c",
          "replace": "Flash",
          "reason": "Stylized spaced letters that should be normalized to standard English spelling"
        },
        {
          "find": "T E S T",
          "replace": "TEST",
          "reason": "Spaced letters forming a word; should be normalized to standard capitalization"
        },
        {
          "find": "The [M \u1d07 \u0262 \u1d00 B \u1d1c s \u1d1b \u1d07 \u0280] weapon",
          "replace": "The [Mega Buster] weapon",
          "reason": "Stylized letters within brackets should be converted to standard English words"
        },
        {
          "find": "REALLY LONG CAPITALIZED TITLE",
          "replace": "Really Long Capitalized Title",
          "reason": "All-caps title should be normalized to sentence case"
        },
        {
          "find": "ANOTHER_WEIRD_CAPS_THING",
          "replace": "Another Weird Caps Thing",
          "reason": "Underscore-separated caps should be converted to readable English words"
        },
        {
          "find": "STRANGE_ACRONYM_EXAMPLE",
          "replace": "Strange Acronym Example",
          "reason": "Non-standard acronym with stylized letters; should be normalized to standard English"
        },
        {
          "find": "U-N-I-T-E-D",
          "replace": "United",
          "reason": "Hyphenated letter sequence should be merged into a single word"
        },
        {
          "find": "S-P-A-C-E-D",
          "replace": "Spaced",
          "reason": "Hyphenated letter sequence should be merged into a single word"
        },
        {
          "find": "F \u029f \u1d00 s \u029c",
          "replace": "Flash",
          "reason": "Duplicate spaced stylized letters; already handled in earlier rule, but deduplication ensures consistency"
        },
        {
          "find": "Q \u1d1c \u026a \u1d04 \u1d0b",
          "replace": "Quick",
          "reason": "Stylized letters forming a word; should be normalized to standard English spelling"
        },
        {
          "find": "CAPS_LOCK_TEXT",
          "replace": "Caps Lock Text",
          "reason": "Underscore-separated caps should be converted to readable English words"
        }
      ]
    },
    {
      "id": 2,
      "range": {
        "start_byte": 1050,
        "end_byte": 1103
      },
      "replacements": []
    }
  ],
  "summary": {
    "unique_problem_words": [
      "F \u029f \u1d00 s \u029c",
      "T E S T",
      "The [M \u1d07 \u0262 \u1d00 B \u1d1c s \u1d1b \u1d07 \u0280] weapon",
      "REALLY LONG CAPITALIZED TITLE",
      "ANOTHER_WEIRD_CAPS_THING",
      "STRANGE_ACRONYM_EXAMPLE",
      "U-N-I-T-E-D",
      "S-P-A-C-E-D",
      "Q \u1d1c \u026a \u1d04 \u1d0b",
      "CAPS_LOCK_TEXT"
    ],
    "replacement_map": {
      "F \u029f \u1d00 s \u029c": "Flash",
      "T E S T": "TEST",
      "The [M \u1d07 \u0262 \u1d00 B \u1d1c s \u1d1b \u1d07 \u0280] weapon": "The [Mega Buster] weapon",
      "REALLY LONG CAPITALIZED TITLE": "Really Long Capitalized Title",
      "ANOTHER_WEIRD_CAPS_THING": "Another Weird Caps Thing",
      "STRANGE_ACRONYM_EXAMPLE": "Strange Acronym Example",
      "U-N-I-T-E-D": "United",
      "S-P-A-C-E-D": "Spaced",
      "Q \u1d1c \u026a \u1d04 \u1d0b": "Quick",
      "CAPS_LOCK_TEXT": "Caps Lock Text"
    }
  }
}
```

## Grammar Results

[DRY RUN] Would process 3 chunks

## Errors

No errors occurred.

## Analysis

[Manual review needed - compare original content with processed results]

---
*Generated by TTS-Proof Simple Test*
