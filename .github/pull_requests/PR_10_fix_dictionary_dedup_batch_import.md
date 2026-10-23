# Pull Request #10: Custom Dictionary Case-Insensitive Deduplication and Batch Comma/Newline Import

## 1. What was the bug before?
In `src/components/tabs/DictionaryTab.tsx`, the `handleAdd` handler had two major usability flaws:
1. **Case-Sensitive Deduplication**: Checked `dictionary.includes(trimmed)`. If the user already had `"Kubernetes"`, entering `"kubernetes"` or `"KUBERNETES"` passed the check and added duplicate entries to the dictionary array. Over time, casing duplicates polluted the dictionary array, increasing fuzzy-matcher evaluation overhead.
2. **Batch Paste Broken**: Users attempting to paste a comma-delimited list of terms (e.g. `"Docker, Kubernetes, Prometheus"`) or multiple lines had the entire block saved as a single literal string (`"Docker, Kubernetes, Prometheus"`), breaking phrase matching in `textproc.py`.
3. **No Quotation Stripping**: Pasting quoted names (e.g. `"FastAPI"` or `'PostgreSQL'`) preserved the quotation marks in the dictionary entry, breaking word boundaries.

## 2. What problem does this PR solve?
- **Case-Insensitive Deduplication**: Compares candidate terms against `new Set(dictionary.map(w => w.toLowerCase()))` to prevent duplicate terms with differing casing.
- **Batch Delimiter Splitting**: Automatically splits inputs across commas (`,`), semicolons (`;`), and newlines (`\n`) so entire lists can be imported in a single action.
- **Quotation Mark Sanitization**: Trims leading and trailing quotes (`"`, `'`, `“`, `”`) from entered terms.
- **Clear Toast Feedback**: Alerts users specifically when terms were added vs skipped due to pre-existing duplicates.

## 3. What is NOT solved / Limitations
- Does not import from external file dialogs (.csv or .txt file picker) - input is via the text input field.

## 4. How was it tested?
- Tested full TypeScript compilation (`npx tsc --noEmit`) - passed with 0 errors.
- Verified batch input `"PostgreSQL, Redis, Docker"` adds 3 distinct terms.
- Verified adding `"redis"` when `"Redis"` is already present is rejected with an informative duplicate notice.
