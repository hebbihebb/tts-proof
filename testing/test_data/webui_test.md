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