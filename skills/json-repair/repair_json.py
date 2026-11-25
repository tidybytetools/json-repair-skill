#!/usr/bin/env python3
"""Repair common broken JSON from AI chats and exports. Standard library only."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SMART = {
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u00ab": '"',
    "\u00bb": '"',
}


def _extract_fence(text: str):
    notes = []
    m = re.search(r"```(?:json|jsonc|javascript|js)?\s*([\s\S]*?)```", text, re.I)
    if m:
        notes.append("pulled JSON out of a markdown code fence")
        return m.group(1).strip(), notes
    return text, notes


def _strip_comments(s: str):
    out = []
    i, n = 0, len(s)
    in_str = False
    quote = ""
    esc = False
    changed = False
    while i < n:
        ch = s[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            i += 1
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and s[i + 1] == "/":
            changed = True
            i += 2
            while i < n and s[i] not in "\n\r":
                i += 1
            continue
        if ch == "/" and i + 1 < n and s[i + 1] == "*":
            changed = True
            i += 2
            while i + 1 < n and not (s[i] == "*" and s[i + 1] == "/"):
                i += 1
            i = min(n, i + 2)
            continue
        out.append(ch)
        i += 1
    return "".join(out), changed


def _drop_trailing_commas(s: str):
    out = []
    i, n = 0, len(s)
    in_str = False
    quote = ""
    esc = False
    changed = False
    while i < n:
        ch = s[i]
        if in_str:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            i += 1
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == ",":
            j = i + 1
            while j < n and s[j] in " \t\r\n":
                j += 1
            if j < n and s[j] in "]}":
                changed = True
                i += 1
                continue
        out.append(ch)
        i += 1
    return "".join(out), changed


def _single_quotes_to_double(s: str):
    if "'" not in s:
        return s, False
    out = []
    i, n = 0, len(s)
    in_dq = False
    esc = False
    changed = False
    while i < n:
        ch = s[i]
        if in_dq:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_dq = False
            i += 1
            continue
        if ch == '"':
            in_dq = True
            out.append(ch)
            i += 1
            continue
        if ch == "'":
            j = i + 1
            chunk = []
            ok = False
            while j < n:
                if s[j] == "\\" and j + 1 < n:
                    nxt = s[j + 1]
                    chunk.append('"' if nxt == "'" else (s[j] + nxt))
                    j += 2
                    continue
                if s[j] == "'":
                    ok = True
                    j += 1
                    break
                if s[j] == '"':
                    chunk.append('\\"')
                    j += 1
                    continue
                if s[j] == "\n":
                    break
                chunk.append(s[j])
                j += 1
            if ok:
                out.append('"')
                out.extend(chunk)
                out.append('"')
                changed = True
                i = j
                continue
        out.append(ch)
        i += 1
    return "".join(out), changed


def _quote_keys(s: str):
    def repl(m):
        return m.group(1) + '"' + m.group(2) + '":'
    new, n = re.subn(r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', repl, s)
    return new, n > 0


def _close_brackets(s: str):
    stack = []
    in_str = False
    quote = ""
    esc = False
    ended_string = False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str = True
            quote = ch
            continue
        if ch in "{[":
            stack.append("}" if ch == "{" else "]")
        elif ch in "}]":
            if stack and stack[-1] == ch:
                stack.pop()
    if in_str:
        s = s + quote
        ended_string = True
    if stack:
        return s + "".join(reversed(stack)), True
    return s, ended_string


def _try_load(s: str):
    try:
        return True, json.loads(s)
    except Exception:
        return False, None


def repair_one(text: str) -> dict:
    notes = []
    raw = (text or "").strip()
    if raw.startswith("\ufeff"):
        raw = raw.lstrip("\ufeff")
        notes.append("removed a byte-order mark")
    if not raw:
        raise ValueError("The JSON text is empty.")

    ok, value = _try_load(raw)
    if ok:
        return {
            "ok": True,
            "wasValid": True,
            "repaired": False,
            "notes": notes,
            "value": value,
            "text": json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        }

    raw, fence_notes = _extract_fence(raw)
    notes.extend(fence_notes)

    for old, new in SMART.items():
        if old in raw:
            raw = raw.replace(old, new)
            if "replaced smart quotes" not in notes:
                notes.append("replaced smart quotes")

    raw2, did = _strip_comments(raw)
    if did:
        raw = raw2
        notes.append("stripped // or /* */ comments")

    lit, nlit = re.subn(r"\bTrue\b", "true", raw)
    lit, nlit2 = re.subn(r"\bFalse\b", "false", lit)
    lit, nlit3 = re.subn(r"\bNone\b", "null", lit)
    if nlit + nlit2 + nlit3:
        raw = lit
        notes.append("swapped Python True/False/None for JSON")

    raw, did = _single_quotes_to_double(raw)
    if did:
        notes.append("swapped single quotes for double quotes")

    raw, did = _quote_keys(raw)
    if did:
        notes.append("quoted unquoted keys")

    raw, did = _drop_trailing_commas(raw)
    if did:
        notes.append("removed trailing commas")

    ok, value = _try_load(raw)
    if ok:
        return {
            "ok": True,
            "wasValid": False,
            "repaired": True,
            "notes": notes,
            "value": value,
            "text": json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        }

    closed, did = _close_brackets(raw)
    if did:
        closed, _ = _drop_trailing_commas(closed)
        ok, value = _try_load(closed)
        if ok:
            notes.append("added missing closing brackets")
            return {
                "ok": True,
                "wasValid": False,
                "repaired": True,
                "notes": notes,
                "value": value,
                "text": json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            }

    chunks = [c.strip() for c in re.split(r"\n\s*\n", raw) if c.strip()]
    if len(chunks) > 1:
        values = []
        all_ok = True
        for c in chunks:
            c2, _ = _drop_trailing_commas(c)
            okc, val = _try_load(c2)
            if not okc:
                all_ok = False
                break
            values.append(val)
        if all_ok:
            notes.append("wrapped several JSON values into one list")
            return {
                "ok": True,
                "wasValid": False,
                "repaired": True,
                "notes": notes,
                "value": values,
                "text": json.dumps(values, ensure_ascii=False, indent=2) + "\n",
            }

    raise ValueError(
        "Could not repair this JSON. Common leftover problems: "
        "truncated strings, mixed-in prose, or invalid numbers."
    )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Repair broken JSON from AI chats and exports. Standard library only."
    )
    p.add_argument("file", help="JSON file, or - for stdin")
    p.add_argument("-o", "--output", help="Write repaired JSON here. Default: print it.")
    p.add_argument("--compact", action="store_true", help="Print one line instead of indented JSON.")
    p.add_argument("--report", action="store_true", help="Also print a short report on stderr.")
    args = p.parse_args(argv)

    if args.file == "-":
        text = sys.stdin.read()
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"error: file not found: {args.file}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8", errors="replace")

    try:
        result = repair_one(text)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    out = result["text"]
    if args.compact:
        out = json.dumps(result["value"], ensure_ascii=False, separators=(",", ":")) + "\n"

    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
    else:
        sys.stdout.write(out)

    if args.report:
        if result["wasValid"]:
            msg = "Already valid JSON. No changes."
        else:
            msg = "Repaired. " + "; ".join(result["notes"])
        print(msg, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
