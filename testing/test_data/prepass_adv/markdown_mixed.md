# Markdown Mixed Content Test

## Heading with CAPS

This tests that Markdown structure remains intact.

### Subheading

Regular paragraph with some SHOUTING words and proper links [like this](https://example.com) that must not be altered.

## Code Blocks

```python
# This code should NOT be processed
VARIABLE = "SHOUTING_CONSTANT"
result = calculate(23 %, 45)
time = "5pm"
```

Inline code like `CONSTANT` and `result=95%` should also be protected.

## Lists

- Item ONE with CAPS
- Item TWO at 3pm
- Item THREE costs 50 %

1. First item at 9am
2. Second IMPORTANT item
3. Third item!!!

## Links and Images

Check [this LINK](https://example.com/CAPS_URL) and ![ALT TEXT](image.png).

The URL https://example.com/test?param=95% should remain unchanged.

## Quoted Text

> This blockquote has SHOUTING and 95 % values!!!
> It also has 5pm times and... ellipsis.

## Tables (if supported)

| HEADING | Value |
|---------|-------|
| DATA    | 95 %  |
| TIME    | 5pm   |

## HTML (should be masked)

<div class="CONTAINER">
  <p>HTML content with 95 % and CAPS!!!</p>
</div>

## Final Paragraph

This ensures all Markdown elements remain structurally intact while TEXT content gets normalized.
