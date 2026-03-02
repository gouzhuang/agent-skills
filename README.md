# Agent Skills

A collection of specialized skills for AI coding agents. Each skill provides documentation and helper scripts for common development tasks.

## Overview

This repository contains standalone skills that can be loaded by agentic coding tools. Each skill is self-contained with documentation and optional helper utilities.

## Repository Structure

```
agent-skills/
├── skills/                # All skills directory
│   ├── pdf/               # PDF processing operations
│   │   ├── SKILL.md       # Skill documentation and usage guide
│   │   ├── forms.md       # PDF form filling documentation
│   │   ├── reference.md   # Extended reference
│   │   └── scripts/       # Python helper scripts
│   └── update-changelog/  # Changelog management
│       └── SKILL.md
├── AGENTS.md              # Coding guidelines for contributors
└── README.md              # Project documentation
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

### Update Changelog (`skills/update-changelog/`)

Guidelines for automatically updating CHANGELOG.md files based on Git changes or session content.

## Usage

Each skill is documented in its `SKILL.md` file. To use a skill:

1. Read the skill's `SKILL.md` for documentation
2. Use helper scripts from the `scripts/` directory when needed

### Running Helper Scripts

```bash
python skills/pdf/scripts/<script_name>.py <arguments>
```

Example:
```bash
python skills/pdf/scripts/convert_pdf_to_images.py input.pdf output_dir/
```

## Dependencies

Python libraries used by helper scripts:
- `pypdf` - PDF manipulation
- `pdfplumber` - Text and table extraction
- `pdf2image` - PDF to image conversion
- `reportlab` - PDF generation
- `Pillow` - Image processing

CLI tools documented:
- `pdftotext` (poppler-utils)
- `qpdf` - PDF manipulation
- `ghostscript` - PDF compression

Install Python dependencies:
```bash
pip install pypdf pdfplumber pdf2image reportlab Pillow
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
