---
name: json-repair
description: Repair broken JSON from AI chats, logs, or exports (trailing commas, smart quotes, comments, single quotes, unquoted keys, markdown fences, truncated brackets, Python True/False/None). Use when the user pastes or shares JSON that fails to parse, or asks to fix, clean, or validate JSON.
license: MIT
---

# Repair broken JSON

The script `repair_json.py` is in the same folder as this file. Python 3.9+, no installs.

## Steps

1. Save the broken text to a file if it is not already one.
2. Run `python3 <this folder>/repair_json.py FILE --report`. It prints valid, indented JSON. The short report goes to stderr.
   - Add `-o fixed.json` to write a file.
   - Add `--compact` for one line.
   - Use `-` as the file name to read from stdin.
3. Tell the user whether it was already valid, and what was fixed (the report lists the steps).
4. If the script exits with an error, say so plainly. Do not invent a fix. Ask for a smaller sample or the original error.

## Notes

- This is a best-effort fixer for common AI and export mistakes. It does not run a full JSON5 parser.
- It will not invent keys or values that were never in the text.
- Truncated strings and mixed-in prose (explanations before or after the JSON, with no code fence) often cannot be repaired.
- Your data stays on the computer. The script never sends the file anywhere.
