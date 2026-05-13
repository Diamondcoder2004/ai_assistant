"""Extract normative PDFs to markdown using PyMuPDF"""
import fitz
import os
import re

pdfs = [
    ('35-fz-ob-elektroenergetike.pdf', '35-fz-ob-elektroenergetike.md'),
    ('861-pravila-tp.pdf', '861-pravila-tp.md'),
    ('442-o-roznichnyh-rynkah.pdf', '442-o-roznichnyh-rynkah.md'),
    ('1178-cenoobrazovanie.pdf', '1178-cenoobrazovanie.md'),
    ('490-22-plata-za-tp.pdf', '490-22-plata-za-tp.md'),
    ('gkt-rb-306-plata-2026.pdf', 'gkt-rb-306-plata-2026.md'),
]

base = 'new_data/source/normative'

for pdf_name, md_name in pdfs:
    pdf_path = os.path.join(base, pdf_name)
    md_path = os.path.join(base, md_name)

    try:
        doc = fitz.open(pdf_path)
        lines = []
        for page in doc:
            text = page.get_text('text')
            if text.strip():
                lines.append(text)

        content = '\n\n'.join(lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)

        # Try to detect headings
        cleaned = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped and len(stripped) < 100:
                is_heading = stripped.isupper() or re.match(r'^[IVXLCDM]+\.', stripped) or re.match(r'^\d+\.\s+[А-Я]', stripped)
                if is_heading:
                    cleaned.append(f'\n## {stripped}\n')
                    continue
            cleaned.append(stripped)

        final = '\n'.join(cleaned)
        title = pdf_name.replace('.pdf', '').replace('-', ' ').title()

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f'# {title}\n\n')
            f.write(final)

        chars = len(final)
        print(f'OK  {pdf_name}: {chars} chars -> {md_name} [{doc.page_count} pages]')
        doc.close()
    except Exception as e:
        print(f'ERR {pdf_name}: {e}')

print('\nDone.')
