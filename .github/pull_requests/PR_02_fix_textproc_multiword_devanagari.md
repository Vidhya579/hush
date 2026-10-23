# Pull Request #2: Support Multi-Word Dictionary Phrases & Unicode Devanagari Script Matching

## 1. What was the bug before?
In `hush/textproc.py`, the dictionary post-correction function `_apply_dictionary` tokenized input text using:
```python
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z']*")
```
This resulted in two severe bugs:
1. **Multi-word phrases ignored**: If a user configured custom multi-word entries (such as `"Hush Engine"`, `"Visual Studio Code"`, or `"San Francisco"`), `_WORD_RE` only passed individual single-word tokens to the matcher. Multi-word phrases could never match and were completely ignored.
2. **Devanagari and non-ASCII character exclusion**: Hush's core feature is English, Hindi, and Hinglish dictation. However, `[A-Za-z]` strictly matched only Latin characters. Any Hindi terms in Devanagari script (e.g. `"नमस्ते"`, `"सूर्यवंश"`) or European names with accents (e.g. `"München"`, `"René"`) were omitted from word extraction and never post-corrected.

## 2. What problem does this PR solve?
- **Multi-Word Phrase Replacement**: Partitions dictionary entries into multi-word phrases and single words. Multi-word phrases are sorted by length (longest first) and replaced with boundary-aware regular expressions.
- **Unicode-Aware Tokenization**: Replaces ASCII `[A-Za-z]` with Unicode letter class `[^\W\d_]+(?:'[^\W\d_]+)?`, allowing Devanagari, Indic, accented, and Latin characters to be matched.
- **Fuzzy Matching for Single Words Preserved**: Maintains high-speed fuzzy matching for single-word vocabulary with canonical case restoration.

## 3. What is NOT solved / Limitations
- Does not transliterate phonetic Romanized Hindi words into Devanagari (e.g., typing "namaste" will not auto-convert to "नमस्ते" unless explicitly mapped in the dictionary).
- Multi-word phrases currently use exact case-insensitive boundary matching rather than token-level fuzzy alignment.

## 4. How was it tested?
- Added `tests/test_textproc.py`:
  - Verified multi-word phrases like `"Hush Engine"` are correctly substituted.
  - Verified Devanagari words like `"नमस्ते"` and `"सूर्यवंश"` are matched and preserved.
  - Verified fuzzy matching for single words (e.g. `"Siryanch"` -> `"Suryansh"`).
- All tests pass (`python -m unittest tests/test_textproc.py`).
