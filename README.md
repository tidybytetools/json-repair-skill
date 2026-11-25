# json-repair-skill

A free agent skill that repairs broken JSON. It works with Claude Code, Cursor, Codex, and any app that reads `SKILL.md` folders.

It fixes the mistakes that show up in AI chat answers and exports: trailing commas, smart quotes, comments, single quotes, unquoted keys, markdown code fences, Python `True`/`False`/`None`, and missing closing brackets. It is one Python file that uses only the standard library (Python 3.9+). No API keys. Your file stays on your computer.

## Install

**Any agent that supports the open skills format:**

```bash
npx skills add tidybytetools/json-repair-skill
```

**GitHub CLI:**

```bash
gh skill install tidybytetools/json-repair-skill
```

**Claude Code plugin marketplace:**

```text
/plugin marketplace add tidybytetools/json-repair-skill
/plugin install json-repair-skill@tidybytetools-skills
```

**By hand:** copy `skills/json-repair/` into `~/.claude/skills/` or `~/.cursor/skills/`, then start a new session and ask: "Repair samples/broken.json."

## Run it without an agent

```bash
python3 skills/json-repair/repair_json.py samples/broken.json --report
```

On the included sample it pulled the JSON out of a code fence, stripped comments, swapped Python `True`, swapped single quotes, quoted unquoted keys, and removed trailing commas, then printed valid JSON.

## Honest limits

This is a best-effort fixer, not a full JSON5 parser. It never invents keys or values. Truncated strings and prose mixed into the JSON often cannot be repaired. When it cannot fix the text, it says so and exits with an error.

## More

- The same repair, as a local command-line tool and MCP server: [`pip install json-repair-lite`](https://pypi.org/project/json-repair-lite/)
- This is one of 8 skills in the [Agent Data Skills Pack](https://tidybyte.gumroad.com/l/agent-data-skills) ($1+, suggested $7): CSV profile, CSV diff, fix garbled characters, split CSV, flatten JSON, redact personal data, chunk Markdown.
- Website: https://tidybytetools.github.io

MIT license. Made by Tidy Byte Tools.
