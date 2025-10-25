# Comprehensive TTS Stress Test — Combined Dataset

This file merges original and web-researched problematic text examples to create a complete TTS normalization and correction benchmark.

---

## SECTION 1 — BASELINE SET (from original compilation)

### 1. Stylized Unicode & Letter Spacing
> “Bʏ Mʏ Rᴇsᴏʟᴠᴇ!” she shouted, her hands glowing with power. “Sᴘɪʀᴀʟ Sᴇᴇᴋᴇʀs!”  
> [M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]  
> “Hᴏɴᴏʀɪɴɢ Vᴀɴɢᴜᴀʀᴅ Dᴇғᴇɴᴅᴇʀ Vᴇʀɪᴛᴀs!”

### 2. Chat Log / Inline Username Format
> [MeanBeanMachine]: Luna! I saw there’s a big attack in Denver! That’s close to you, right? Are you okay!?  
> [LunaLightOTK]: I’m fine, Bean. The kaiju’s headed away from me.  
> [MeanBeanMachine]: ALL of them!? WHAT!?!?!?

### 3. Onomatopoeia, Emphasis, and All-Caps
> “Aaahahaha! No way—NO WAY!”  
> The crash went *BANG!* then “uhhh...” silence.  
> “AAAAAAA stop stop stop!” she screamed.  
> bluh... Bluh... BLUH!

### 4. Nested Parentheses and Ellipses
> She muttered quietly (or maybe not so quietly (honestly it was more of a shout...)) before slumping.  
> “I’m fine... probably... maybe...”

### 5. Multi-Unit Data and Scientific Notation
> Temperature reading: sixty‑three point eight degrees Fahrenheit (that’s seventeen point six Celsius, which is four hundred and fourteen point one Pyulor).  
> Power reserves at 23%. Estimated runtime thirteen minutes at maximum specs.

### 6. Code-Like or System Text
```
Status: INACTIVE
Error: Undefined variable 'soul_core'
Runtime: 13m 42s
> Reinitializing process...
```

### 7. Mixed Em Dashes, Hyphens, and Dot Chains
> “It’s—well—it’s just... I mean...—”  
> “Wait––you mean the *real* one–?”  
> “I... I... I didn’t––I couldn’t––”

### 8. Foreign or Non-English Insertions
> “¡Lᴀs Pʀᴏᴛᴇɢᴇʀᴇ́!” she cried.  
> “Je ne sais pas... maybe?”  
> “Danke schön—uh, thanks.”

### 9. Scene Dividers and Symbolic Breaks
> ***  
> ~~~  
> —–—

### 10. Emotional Fragmentation and Stuttered Speech
> “I— I didn’t mean—wait, no, I *did* mean—uh—sorry.”  
> “It’s... fine... really... fine.”  
> “Wh-what do you mean by *recalibration*?”

### 11. Improper Quotation Nesting
> “‘She said “go away,”’ I repeated,” she muttered.  
> “He told me, ‘Don’t.’”

### 12. Emotionless System Narration
> Power reserves increased from 23% to 24%.  
> Core temperature stable at 391 Pyulor.  
> Emotional burn rate elevated.

### 13. Typos and Glitches
> “She’s just... soso... so weird.”  
> “It tturns out it’s fine.”  
> “Ugh,, yeah no that’s... fine?”  
> “whY are YOU like this”

### 14. Long Run-On Dialogue
> “You think you can just walk in here after everything and pretend like nothing happened and maybe you’re right and maybe I’m just too tired to care anymore but god it hurts, it hurts so much I can’t even—”

### 15. Encoded Scene Mix (Full Stress Test)
> “¡Fᴜᴇʀᴢᴀ Aʀᴅɪᴇɴᴛᴇ!” Veritas yelled, the temperature reading sixty‑three point eight Fahrenheit (seventeen point six Celsius). [LunaLightOTK]: *uhhh... bluh...* “AAAH––NOOOO!” *** “Reinitializing process...” Runtime: 13m 42s. Power 23%. “Je ne sais pas,” she whispered.

---

## SECTION 2 — WEB SOURCED EXPANSIONS

### 16. Abbreviations & Ambiguous Expansions
> “Dr. Brown arrived at 5 p. m. to meet Mr. O’Connor at St. Mary’s.”  
> “I live on 123 NW 5th St.”

### 17. Fractions, Ratios, and Slash Syntax
> “1/2 of the team passed.”  
> “The ratio is 3:4.”  
> “He scored 5/8 in the test.”

### 18. Currency / Monetary Formats
> “The price is $3.50.”  
> “Earned €1,200.75 last quarter.”  
> “He owes ¥8000.”

### 19. Mixed-Direction / Bidirectional Text
> "John asked: שלום John, how are you?"  
> “Here is English and then עברית embedded.”

### 20. Emoji, Emoticons, and Symbols Mid-Sentence
> “She typed: I’m so happy 😊 but also tired.”  
> “He said >:( and walked away.”

### 21. High Repetition / Repeated Characters or Diacritics
> “So coooolllll!”  
> “Noooooooo...”  
> “He said ééẽewww.”

### 22. Malformed Unicode / ZWJ / Invisible Characters
> “café” vs “café” (different composition)  
> “Th​is has zero‑width space here.”

### 23. Non‑Standard Tokens: URLs, Email, Hashtags, Handles
> “Go see https://example. com/test? ref=42”  
> “Contact me at someone@domain. io”  
> “#ThrowbackThursday was lit.”  
> “@username replied.”

### 24. Ordinal vs Cardinal Ambiguity
> “He came in 1st place.”  
> “The date is 11/12/13.”

### 25. Nested Parentheses and Bracketed Tiers (Complex)
> “He claimed (though skeptics disagree (and for good reason)) that it’s true.”  
> “She sang [in a whisper (so soft it barely reached me)] before falling silent.”

### 26. Ellipses with Spaces / Dot Clusters
> “Well... I guess so.”  
> “Wait...what?”  
> “He trailed off with ... ... ...”

### 27. Non‑English / Transliteration + Diacritics
> “¡Qué será, será!”  
> “Götterdämmerung”  
> “東京 (Tokyo) is amazing.”

### 28. Temporal Expressions & Durations
> “He arrived at 09:05:30.”  
> “In 2h 45m he’ll depart.”  
> “The meeting is on 12/24/2025 at 14:30.”

### 29. Homographs / Heteronyms Depending on Context
> “He *recorded* the record.”  
> “She will *lead* the lead.”  
> “He wound the wind‑up toy.”

### 30. Punctuation Read-Out / Punctuation Confusion
> “Wait... what?”  
> “Do you mean “. NET” or “dot net”?”  
> “End.” (a single word)

---

End of File — *Total: 30 categories of TTS / normalization stressors.*
