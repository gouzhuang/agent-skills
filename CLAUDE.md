# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A collection of standalone skills for AI coding agents. Each skill is a self-contained directory under `skills/` with documentation (`SKILL.md`) and optional helper scripts.

## Current Skills

- **pdf** — PDF processing (merge, split, extract, OCR, form filling, background cleaning). Based on [Anthropic's skills repo](https://github.com/anthropics/skills).
- **loinc-query** — LOINC medical terminology database queries via Regenstrief Search API. Requires `httpx` and credentials in `~/.loincrc` or env vars `LOINC_USERNAME`/`LOINC_PASSWORD`.
- **update-changelog** — Auto-update CHANGELOG.md from git staged changes or session content.

## Skill Structure Convention

```
skills/<skill-name>/
├── SKILL.md              # Required: frontmatter (name, description) + documentation
├── references/           # Optional: supplementary docs
└── scripts/              # Optional: standalone Python helper scripts
```

## Running Scripts

No build system. Scripts are standalone Python run directly:
```bash
python skills/pdf/scripts/<script>.py <args>
python skills/loinc-query/scripts/loinc_search.py search "glucose"
```

## Python Script Conventions

- 4-space indent, ~100 char line limit, double quotes for strings
- Imports: stdlib first, third-party second, no local imports (scripts are standalone)
- CLI via `argparse`; JSON to stdout, errors to stderr; `sys.exit(1)` on failure
- No type hints used in this codebase
- No try/except for common errors — let them bubble up

## Adding a New Skill

1. `mkdir skills/<name>/`
2. Create `SKILL.md` with YAML frontmatter (`name`, `description`, optional `license`)
3. Add `scripts/` directory with standalone Python scripts if needed
4. Document dependencies and include usage examples

## Key Dependencies

- `pypdf`, `pdfplumber`, `pdf2image`, `reportlab`, `Pillow`, `numpy` — PDF skill
- `httpx` — LOINC query skill
- CLI tools: `pdftotext` (poppler-utils), `qpdf`, `ghostscript`

## Language Notes

Documentation is written in both English and Chinese. The loinc-query and update-changelog SKILL.md files are primarily in Chinese.
