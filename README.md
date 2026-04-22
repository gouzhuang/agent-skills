# Agent Skills

A collection of specialized skills for AI coding agents. Each skill provides documentation and helper scripts for common development tasks.

## Overview

This repository contains standalone skills that can be loaded by agentic coding tools. Each skill is self-contained with documentation and optional helper utilities.

## Repository Structure

```
agent-skills/
├── skills/                    # All skills directory
│   ├── pdf/                   # PDF processing operations
│   │   ├── SKILL.md           # Skill documentation and usage guide
│   │   ├── forms.md           # PDF form filling documentation
│   │   ├── reference.md       # Extended reference
│   │   └── scripts/           # Python helper scripts
│   ├── loinc-query/           # LOINC medical terminology queries
│   │   ├── SKILL.md           # Skill documentation
│   │   ├── references/        # Search syntax reference
│   │   └── scripts/           # Query helper scripts
│   ├── privacy-review/        # Privacy data leakage scanner
│   │   ├── SKILL.md           # Skill documentation
│   │   └── scripts/           # Scanner helper scripts
│   └── update-changelog/      # Changelog management
│       └── SKILL.md
├── AGENTS.md                  # Coding guidelines for contributors
└── README.md                  # Project documentation
```

## Available Skills

### PDF Processing (`skills/pdf/`)

Complete guide for PDF operations including:
- Merging, splitting, and rotating PDFs
- Text and table extraction
- PDF form filling
- OCR on scanned documents
- PDF compression and optimization
- Adding watermarks and encryption
- Background noise cleaning for scanned PDFs

This skill is developed based on the PDF skill from [Anthropic's skills repository](https://github.com/anthropics/skills).

**Helper Scripts:**
- `fill_pdf_form_with_annotations.py` - Fill PDF forms with text annotations
- `convert_pdf_to_images.py` - Convert PDF pages to PNG images
- `extract_form_structure.py` - Extract form structure from non-fillable PDFs
- `check_fillable_fields.py` - Analyze fillable form fields
- `extract_form_field_info.py` - Extract field information from PDFs
- `fill_fillable_fields.py` - Fill native PDF form fields
- `create_validation_image.py` - Create validation images for form fields
- `check_bounding_boxes.py` - Validate bounding box coordinates
- `clean_pdf_background.py` - Clean background noise from scanned PDFs

### LOINC Query (`skills/loinc-query/`)

Query the LOINC medical terminology database via the Regenstrief Search API:
- Search LOINC terms with advanced syntax (field restrictions, boolean operators, wildcards)
- Look up LOINC parts, answer lists, and groups
- View detailed information for specific LOINC codes
- Structured JSON output with summary and results

Requires `httpx` and LOINC credentials (`~/.loincrc` or env vars `LOINC_USERNAME`/`LOINC_PASSWORD`).

**Helper Scripts:**
- `loinc_search.py` - Search and query LOINC database

### Privacy Review (`skills/privacy-review/`)

Scan codebases for privacy data leakage risks:
- Detect hardcoded secrets, API keys, passwords, private keys
- Find database connection strings, JWT tokens
- Identify email addresses, phone numbers, ID cards
- Filter by severity level (high/medium/low)
- JSON and text output formats

**Helper Scripts:**
- `privacy_review.py` - Scan directories for privacy data leakage

### Update Changelog (`skills/update-changelog/`)

Guidelines for automatically updating CHANGELOG.md files based on Git changes or session content.

## Usage

Each skill is documented in its `SKILL.md` file. To use a skill:

1. Read the skill's `SKILL.md` for documentation
2. Use helper scripts from the `scripts/` directory when needed

### Running Helper Scripts

```bash
python skills/<skill-name>/scripts/<script_name>.py <arguments>
```

Examples:
```bash
# PDF: Convert PDF pages to images
python skills/pdf/scripts/convert_pdf_to_images.py input.pdf output_dir/

# LOINC: Search for glucose terms
python skills/loinc-query/scripts/loinc_search.py search "glucose"

# Privacy: Scan current directory for leaks
python skills/privacy-review/scripts/privacy_review.py .
```

## Dependencies

### PDF Skill
Python libraries:
- `pypdf` - PDF manipulation
- `pdfplumber` - Text and table extraction
- `pdf2image` - PDF to image conversion
- `reportlab` - PDF generation
- `Pillow` - Image processing
- `numpy` - Image processing (background cleaning)

CLI tools:
- `pdftotext` (poppler-utils)
- `qpdf` - PDF manipulation
- `ghostscript` - PDF compression

### LOINC Query Skill
- `httpx` - HTTP client for API requests

Install Python dependencies:
```bash
pip install pypdf pdfplumber pdf2image reportlab Pillow numpy httpx
```

## Contributing

To add a new skill:

1. Create a new directory: `mkdir skills/new-skill/`
2. Add `SKILL.md` with frontmatter:
   ```yaml
   ---
   name: skill-name
   description: "Clear description of what this skill does"
   ---
   ```
3. Add helper scripts in `skills/new-skill/scripts/` if needed
4. Follow the code style guidelines in `AGENTS.md`
5. Document all dependencies
6. Include usage examples

## License

See individual skill directories for license information.
