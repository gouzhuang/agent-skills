# Agentic Coding Guidelines

This repository contains agent skills (documentation and helper scripts). Each skill is a self-contained directory with a `SKILL.md` file and optional helper scripts.

## Repository Structure

```
agent-skills/
├── skills/                       # All skills directory
│   ├── pdf/                      # PDF processing skill
│   │   ├── SKILL.md              # Skill documentation
│   │   ├── forms.md              # Form-specific documentation
│   │   ├── reference.md          # Extended reference
│   │   └── scripts/              # Python helper scripts
│   │       ├── fill_pdf_form_with_annotations.py
│   │       ├── convert_pdf_to_images.py
│   │       └── ...
│   └── update-changelog/         # Changelog skill
│       └── SKILL.md
├── AGENTS.md                     # Coding guidelines
└── README.md                     # Project documentation
```

## Build/Test/Lint Commands

**No build system configured.** This is a documentation and script repository without formal build tooling.

- No package.json, pyproject.toml, or Makefile exists
- No automated tests exist
- No linting configuration exists
- Python scripts are standalone utilities

To test a Python script manually:
```bash
python skills/pdf/scripts/<script_name>.py <args>
```

## Code Style Guidelines

### Python Scripts

**Formatting:**
- 4-space indentation
- Maximum line length: ~100 characters (soft limit)
- Double quotes for strings
- Two blank lines between top-level functions/classes
- One blank line between methods

**Naming Conventions:**
- `snake_case` for functions, variables, modules
- `PascalCase` for classes (if any)
- `UPPER_CASE` for constants (rarely used)

**Imports:**
```python
# Standard library first
import json
import sys
import os

# Third-party libraries second
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText
import pdfplumber

# No local imports (scripts are standalone)
```

**Function Structure:**
```python
def function_name(arg1, arg2):
    """Docstring describing what the function does."""
    # Implementation
    pass


def main():
    if len(sys.argv) != 3:
        print("Usage: script.py <arg1> <arg2>")
        sys.exit(1)
    # Main logic


if __name__ == "__main__":
    main()
```

**Error Handling:**
- Check argument counts explicitly
- Use `sys.exit(1)` for CLI errors
- No try/except blocks for common errors (let them bubble up)
- Print helpful usage messages

**Type Hints:** Not currently used in this codebase.

### SKILL.md Files

**Frontmatter Format:**
```yaml
---
name: skill-name
description: "Clear description of what this skill does"
license: Proprietary. LICENSE.txt has complete terms  # if applicable
---
```

**Documentation Style:**
- Clear hierarchical headings (H1, H2, H3)
- Code blocks with language tags (```python, ```bash)
- Tables for quick reference
- Examples should be copy-paste ready
- Use "## Quick Reference" tables for common operations

## Dependencies

Python scripts use these libraries:
- `pypdf` - PDF manipulation
- `pdfplumber` - Text and table extraction
- `pdf2image` - PDF to image conversion
- `reportlab` - PDF generation (documented, not scripted)
- `Pillow` - Image processing (via pdf2image)

CLI tools documented:
- `pdftotext` (poppler-utils)
- `qpdf` - PDF manipulation
- `ghostscript` - PDF compression

## Writing New Skills

1. Create directory: `mkdir skills/new-skill/`
2. Create `skills/new-skill/SKILL.md` with frontmatter
3. Add helper scripts in `skills/new-skill/scripts/` if needed
4. Follow existing naming conventions
5. Document dependencies clearly
6. Include usage examples

## Git Workflow

- No CI/CD configured
- No pre-commit hooks
- Commit messages should be descriptive
- Skills are standalone - changes to one shouldn't break others
