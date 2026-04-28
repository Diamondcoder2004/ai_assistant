---
name: doc-specialist
description: Document operations specialist — convert, create, edit, and analyze office formats (DOCX, PDF, PPTX). Handles markdown-to-office, office-to-markdown, document generation, form filling, and tracked changes. Use when user asks to create a Word document, PDF, presentation, or convert between formats.
---

# Document Operations Specialist

Orchestrates all office document work: conversions, creation, editing, and analysis between Markdown and office formats (DOCX, PDF, PPTX).

## When to Use This Skill

- "Convert this markdown to a Word document"
- "Create a PDF report from this text"
- "Extract text from this .docx file"
- "Make a presentation from these notes"
- "Fill out this PDF form"
- "Edit this existing document"

## Available Skills

| Skill | What it does |
|-------|-------------|
| `docx` | Create/edit Word documents, tracked changes, comments, professional formatting |
| `pdf` | Read, create, merge, split, fill forms, watermark, OCR |
| `pptx` | Create/edit presentations, work with templates, export to images |

---

## Workflow: Markdown → DOCX

1. Load the `docx` skill
2. Use `docx-js` (Node.js) to create the document:
   - Set page size explicitly (A4 or US Letter)
   - Use Arial as default font
   - Apply heading styles with `HeadingLevel`
   - Use numbered lists with `LevelFormat.DECIMAL`, never unicode bullets
   - Tables need both `columnWidths` and cell `width` with `WidthType.DXA`
3. Validate: `python scripts/office/validate.py output.docx`
4. Report the file path

## Workflow: DOCX → Markdown

1. Read with pandoc: `pandoc --track-changes=all input.docx -o output.md`
2. For complex documents or XML editing:
   - Unpack: `python scripts/office/unpack.py input.docx unpacked/`
   - Edit XML in `unpacked/word/document.xml`
   - Pack: `python scripts/office/pack.py unpacked/ output.docx --original input.docx`

## Workflow: Markdown → PDF

Preferred path: Markdown → DOCX → PDF
1. Create DOCX as above, then convert:
   `python scripts/office/soffice.py --headless --convert-to pdf document.docx`
2. Alternative: use `pypdf` or `markitdown` for direct creation

## Workflow: PDF → Markdown

1. Simple text: `python -m markitdown input.pdf`
2. Complex/forms: use the `pdf` skill with `pypdf`

## Workflow: Markdown → PPTX

1. Load the `pptx` skill
2. For new decks: use `pptxgenjs` (Node.js)
3. For templates: use the `editing.md` guide in the pptx skill

## Workflow: PPTX → Markdown

1. `python -m markitdown presentation.pptx`

---

## Cross-cutting Rules

- **Always validate** after creating documents (docx: `validate.py`, pdf: `pypdf` reader check)
- **UTF-8 everywhere** — all text is UTF-8; CSV files use UTF-8-sig BOM
- **Professional formatting**: sans-serif fonts, consistent headings, proper table styles
- **When in doubt about formatting**, ask the user: "Should I use A4 or US Letter? Any specific brand colors or fonts?"
