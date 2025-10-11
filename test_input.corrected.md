# TTS Prepass Test Document

This document contains various patterns that are problematic for text-to-speech engines.

## Spaced and Stylized Letters

The Flash Dance technique is very effective.

Some TEST content with spacing issues.

The [Mega Buster] weapon is powerful.

## Weird Capitalization

This Really Long Capitalized Title needs normalization.

Another Weird Caps Thing should be fixed.

NASA and GPU are valid acronyms, but Strangely, this is not a valid acronym.

## Hyphenated Letter Sequences

The United States of A-M-E-R-I-C-A.

Some Spaced words here.

## Mixed Problems

More Flash content to test deduplication.

The Quick brown fox jumps.

Some Caps Lock Text and more issues.

## Normal Text

This paragraph should not trigger any TTS problems. It contains normal text with proper capitalization, standard punctuation, and regular word spacing. This serves as a control to ensure the prepass detector only flags actual problems.

The code blocks should also be ignored:
```javascript
const CAPS_IN_CODE = "should be ignored";
const spaced_variable = F_L_A_S_H_DANCE;
```
And inline code like `CAPS_CODE` should be preserved.
