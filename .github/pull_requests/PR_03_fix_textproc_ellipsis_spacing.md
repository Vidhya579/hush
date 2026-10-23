# Pull Request #3: Preserve Ellipses and Fix Punctuation Spacing Around Numbers, Quotes, and Unicode

## 1. What was the bug before?
In `hush/textproc.py`, the `_repair` function cleaned text with two problematic regex operations:
```python
text = re.sub(r"([,.!?;:])(?=[A-Za-z])", r"\1 ", text)  # one space after
text = re.sub(r"([,.!?;:]){2,}", r"\1", text)         # collapse doubled punctuation
```
This produced the following bugs:
1. **Ellipses destruction**: Intentional trailing thought pauses or standard Whisper-generated ellipses (`...` or Unicode `…`) matched `([,.!?;:]){2,}` and were collapsed into a single period (`.`). E.g. `"Wait a minute... let me think"` became `"Wait a minute. Let me think"`.
2. **Missing spaces before numbers**: `(?=[A-Za-z])` strictly matched Latin letters only. Dictations like `"items 1,2,3"` remained cramped as `"items 1,2,3"`.
3. **Missing spaces before quotes & Unicode**: If Whisper emitted punctuation directly attached to quotes or Hindi text (e.g. `said,"hello"` or `नमस्ते,भारत`), no space was inserted.

## 2. What problem does this PR solve?
- **Ellipsis Protection**: Shields `...` and Unicode `…` using a sentinel placeholder before punctuation normalization, then restores standard three-dot ellipses afterwards.
- **Selective Doubled Punctuation Collapse**: Collapses unintentional repeated punctuation (e.g., `,,`, `??`, `!!`, or doubled `..`) while keeping three-dot ellipses intact.
- **Comprehensive Spacing**: Inserts appropriate spacing after punctuation when followed by Unicode word characters, opening quotes, brackets, or numbers (while properly preserving floating-point decimals like `3.14`).

## 3. What is NOT solved / Limitations
- Does not change Whisper's native acoustic pause detection threshold.
- Does not alter complex typographic hyphen/dash combinations (e.g., em-dash `—` or en-dash `–`).

## 4. How was it tested?
- Added `tests/test_ellipsis.py` covering:
  - Preserving standard `...` pauses.
  - Converting Unicode `…` to standard `...`.
  - Collapsing duplicate punctuation (`,,` -> `,`).
  - Spacing lists of numbers (`1, 2, 3`).
  - Preserving mathematical decimals (`3.14`).
- All 5 test cases pass cleanly.
