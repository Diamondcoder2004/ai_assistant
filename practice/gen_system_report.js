const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat,
        HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: '000000' };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function makeCell(text, opts = {}) {
  const { bold = false, size = 22, fill = null, align = AlignmentType.LEFT } = opts;
  return new TableCell({
    borders,
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({ text, size, bold, font: 'Times New Roman' })],
      alignment: align,
    })]
  });
}

function p(text, opts = {}) {
  const { size = 24, bold = false, italics = false, align = AlignmentType.JUSTIFIED, numbering = null, spacing = { after: 120 } } = opts;
  return new Paragraph({
    children: [new TextRun({ text, size, bold, italics, font: 'Times New Roman' })],
    alignment: align,
    numbering,
    spacing,
  });
}

function heading(level, text) {
  const h = level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;
  return new Paragraph({ heading: h, children: [new TextRun({ text, font: 'Times New Roman' })] });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Times New Roman', size: 28 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Times New Roman', color: '000000' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0, alignment: AlignmentType.CENTER } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Times New Roman', color: '000000' },
        paragraph: { spacing: { before: 180, after: 60 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Times New Roman', color: '000000' },
        paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: 'bullets',
        levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2013', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        children: [new TextRun({ text: '\u0418\u043d\u0442\u0435\u043b\u043b\u0435\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442 \u0411\u0430\u0448\u043a\u0438\u0440\u044d\u043d\u0435\u0440\u0433\u043e', size: 20, bold: true, font: 'Times New Roman' })],
        alignment: AlignmentType.CENTER,
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        children: [new TextRun({ text: '\u0421\u0442\u0440\u0430\u043d\u0438\u0446\u0430 ', size: 20, font: 'Times New Roman' }), new TextRun({ children: [PageNumber.CURRENT], size: 20, font: 'Times New Roman' })],
        alignment: AlignmentType.CENTER,
      })] })
    },
    children: [
      // TITLE PAGE
      new Paragraph({ spacing: { before: 3600 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u0418\u043d\u0442\u0435\u043b\u043b\u0435\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442', size: 48, bold: true, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { after: 240 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0437\u0430\u0446\u0438\u044f \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0439 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0438', size: 32, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { after: 240 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u043f\u043e \u0443\u0441\u043b\u0443\u0433\u0435 \u00ab\u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043f\u0440\u0438\u0441\u043e\u0435\u0434\u0438\u043d\u0435\u043d\u0438\u0435\u00bb', size: 32, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { before: 1200 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0441\u0438\u0441\u0442\u0435\u043c\u044b \u0438 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f', size: 28, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { after: 120 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u041e\u0442\u0447\u0451\u0442 \u043f\u043e \u043f\u0440\u0430\u043a\u0442\u0438\u043a\u0435', size: 24, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { after: 120 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u0410\u043f\u0440\u0435\u043b\u044c 2026', size: 24, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { before: 1200 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u041e\u041e\u041e \u00ab\u0411\u0430\u0448\u043a\u0438\u0440\u044d\u043d\u0435\u0440\u0433\u043e\u00bb', size: 24, bold: true, font: 'Times New Roman' })] }),
      new Paragraph({ spacing: { before: 200 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u0414\u0435\u043f\u0430\u0440\u0442\u0430\u043c\u0435\u043d\u0442 \u0431\u0438\u0437\u043d\u0435\u0441-\u0441\u0438\u0441\u0442\u0435\u043c (\u0414\u0411\u0421)', size: 22, font: 'Times New Roman' })] }),

      new Paragraph({ children: [new PageBreak()] }),

      // ===== 1. НАЗНАЧЕНИЕ =====
      heading(1, '1. \u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435 \u0441\u0438\u0441\u0442\u0435\u043c\u044b'),
      p('\u0418\u043d\u0442\u0435\u043b\u043b\u0435\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0430\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442 \u043f\u0440\u0435\u0434\u043d\u0430\u0437\u043d\u0430\u0447\u0435\u043d \u0434\u043b\u044f \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0437\u0430\u0446\u0438\u0438 \u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0439 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0438 \u043f\u043e\u0442\u0440\u0435\u0431\u0438\u0442\u0435\u043b\u0435\u0439 \u043f\u043e \u0443\u0441\u043b\u0443\u0433\u0435 \u00ab\u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u043e\u0435 \u043f\u0440\u0438\u0441\u043e\u0435\u0434\u0438\u043d\u0435\u043d\u0438\u0435 \u043a \u044d\u043b\u0435\u043a\u0442\u0440\u0438\u0447\u0435\u0441\u043a\u0438\u043c \u0441\u0435\u0442\u044f\u043c \u041e\u041e\u041e \u0411\u0430\u0448\u043a\u0438\u0440\u044d\u043d\u0435\u0440\u0433\u043e\u00bb. \u0421\u0438\u0441\u0442\u0435\u043c\u0430 \u043e\u0442\u0432\u0435\u0447\u0430\u0435\u0442 \u043d\u0430 \u0432\u043e\u043f\u0440\u043e\u0441\u044b \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432, \u043f\u0440\u0435\u0434\u043e\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442 \u043f\u043e\u0448\u0430\u0433\u043e\u0432\u044b\u0435 \u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u0438, \u0440\u0430\u0441\u0441\u0447\u0438\u0442\u044b\u0432\u0430\u0435\u0442 \u0441\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f \u0438 \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u044f\u0435\u0442 \u0437\u0430\u044f\u0432\u043a\u0438.'),
      p('\u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u0444\u043e\u0440\u043c\u0438\u0440\u0443\u0435\u0442\u0441\u044f \u0438\u0437 22 \u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0445 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432, \u0432\u043a\u043b\u044e\u0447\u0430\u044f \u0424\u0417-35, \u041f\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 861, \u043f\u0430\u0441\u043f\u043e\u0440\u0442\u0430 \u0443\u0441\u043b\u0443\u0433, \u0432\u043d\u0443\u0442\u0440\u0435\u043d\u043d\u0438\u0435 \u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u0438 \u0438 \u0442\u0430\u0440\u0438\u0444\u043d\u044b\u0435 \u0441\u0442\u0430\u0432\u043a\u0438.'),

      // ===== 2. АРХИТЕКТУРА =====
      heading(1, '2. \u0410\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u0430 \u0441\u0438\u0441\u0442\u0435\u043c\u044b'),
      p('\u0421\u0438\u0441\u0442\u0435\u043c\u0430 \u043f\u043e\u0441\u0442\u0440\u043e\u0435\u043d\u0430 \u043d\u0430 \u0430\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u0435 Agentic RAG (Retrieval-Augmented Generation) \u0441 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435\u043c \u0442\u0440\u0451\u0445 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u0430\u0433\u0435\u043d\u0442\u043e\u0432:'),

      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2500, 6526],
        rows: [
          new TableRow({
            children: [
              makeCell('\u0410\u0433\u0435\u043d\u0442', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
              makeCell('\u0424\u0443\u043d\u043a\u0446\u0438\u044f', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Query Generator', { bold: true, fill: 'F5F5F5' }),
              makeCell('\u041a\u043b\u0430\u0441\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f \u0432\u043e\u043f\u0440\u043e\u0441\u0430: \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0441\u044f \u043b\u0438 \u043a \u0422\u041f? \u0414\u0435\u043a\u043e\u043c\u043f\u043e\u0437\u0438\u0446\u0438\u044f \u0441\u043b\u043e\u0436\u043d\u044b\u0445 \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432. \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430 \u0432\u0435\u0441\u043e\u0432 \u043f\u043e\u0438\u0441\u043a\u0430.', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Search Agent', { bold: true }),
              makeCell('\u0413\u0438\u0431\u0440\u0438\u0434\u043d\u044b\u0439 \u043f\u043e\u0438\u0441\u043a: 3 \u0441\u0435\u043c\u0430\u043d\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0445 \u0432\u0435\u043a\u0442\u043e\u0440\u0430 (PREF, HYPE, CONTEXTUAL) + \u043b\u0435\u043a\u0441\u0438\u0447\u0435\u0441\u043a\u0438\u0439 BM25. \u041d\u043e\u0440\u043c\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f score/max_score.'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Response Agent', { bold: true, fill: 'F5F5F5' }),
              makeCell('\u0413\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u0444\u0438\u043d\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u043e\u0442\u0432\u0435\u0442\u0430 \u043d\u0430 \u043e\u0441\u043d\u043e\u0432\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043d\u043e\u0433\u043e \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442\u0430. \u0424\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u043e\u0442\u0432\u0435\u0442\u0430 \u0441\u043e \u0441\u0441\u044b\u043b\u043a\u0430\u043c\u0438 \u043d\u0430 \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0438.', { fill: 'F5F5F5' }),
            ]
          }),
        ]
      }),

      new Paragraph({ children: [new PageBreak()] }),

      // ===== 3. ТЕХНОЛОГИИ =====
      heading(1, '3. \u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u0438\u0439 \u0441\u0442\u0435\u043a'),

      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2500, 6526],
        rows: [
          new TableRow({
            children: [
              makeCell('\u041a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
              makeCell('\u0422\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Backend', { bold: true, fill: 'F5F5F5' }),
              makeCell('Python 3.11+, FastAPI, Uvicorn', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Frontend', { bold: true }),
              makeCell('Vue.js 3, Vite, Pinia, Vue Router'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Vector DB', { bold: true, fill: 'F5F5F5' }),
              makeCell('Qdrant', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('RDBMS + Auth', { bold: true }),
              makeCell('Supabase (PostgreSQL + Auth)'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('LLM', { bold: true, fill: 'F5F5F5' }),
              makeCell('RouterAI \u2014 Inception/Mercury 2 (>1000 \u0442\u043e\u043a\u0435\u043d\u043e\u0432/\u0441\u0435\u043a, \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 128K)', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Embeddings', { bold: true }),
              makeCell('pplx-embed-v1-4b (Perplexity, 4096 \u0438\u0437\u043c\u0435\u0440\u0435\u043d\u0438\u0439)'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('\u041f\u043e\u0438\u0441\u043a', { bold: true, fill: 'F5F5F5' }),
              makeCell('rank-bm25, pymorphy3 (\u043b\u0435\u043c\u043c\u0430\u0442\u0438\u0437\u0430\u0446\u0438\u044f)', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('\u041a\u043e\u043d\u0442\u0435\u0439\u043d\u0435\u0440\u0438\u0437\u0430\u0446\u0438\u044f', { bold: true }),
              makeCell('Docker + Docker Compose'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Reverse Proxy', { bold: true, fill: 'F5F5F5' }),
              makeCell('Nginx', { fill: 'F5F5F5' }),
            ]
          }),
        ]
      }),

      // ===== 4. АППАРАТНЫЕ =====
      heading(1, '4. \u0410\u043f\u043f\u0430\u0440\u0430\u0442\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f'),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3500, 5526],
        rows: [
          new TableRow({
            children: [
              makeCell('\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
              makeCell('\u0422\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u0435', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('CPU', { bold: true, fill: 'F5F5F5' }),
              makeCell('4 \u044f\u0434\u0440\u0430 (4 vCPU)', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('RAM', { bold: true }),
              makeCell('4\u20138 \u0413\u0411'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('\u0414\u0438\u0441\u043a', { bold: true, fill: 'F5F5F5' }),
              makeCell('10+ \u0413\u0411 (\u0434\u043b\u044f Qdrant, \u0411\u0414, \u043b\u043e\u0433\u043e\u0432)', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('\u0421\u0435\u0442\u044c', { bold: true }),
              makeCell('\u0414\u043e\u0441\u0442\u0443\u043f \u043a RouterAI API (\u043e\u0431\u043b\u0430\u043a\u043e), \u043f\u043e\u0440\u0442\u044b 8877 (frontend), 8880 (backend), 6333 (Qdrant)'),
            ]
          }),
        ]
      }),

      // ===== 5. СТОИМОСТЬ =====
      heading(1, '5. \u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c \u044d\u043a\u0441\u043f\u043b\u0443\u0430\u0442\u0430\u0446\u0438\u0438'),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3500, 5526],
        rows: [
          new TableRow({
            children: [
              makeCell('\u041a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
              makeCell('\u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('LLM API (RouterAI)', { bold: true, fill: 'F5F5F5' }),
              makeCell('~300\u2013800 \u0440\u0443\u0431/\u043c\u0435\u0441 (\u043f\u0440\u0438 100 \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432/\u0434\u0435\u043d\u044c)', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('VPS (4 vCPU / 8 \u0413\u0411)', { bold: true }),
              makeCell('~1500\u20133000 \u0440\u0443\u0431/\u043c\u0435\u0441'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('Qdrant', { bold: true, fill: 'F5F5F5' }),
              makeCell('\u0412\u043a\u043b\u044e\u0447\u0435\u043d\u043e \u0432 VPS (self-hosted)', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('\u0418\u0442\u043e\u0433\u043e', { bold: true }),
              makeCell('~1800\u20133800 \u0440\u0443\u0431/\u043c\u0435\u0441', { bold: true }),
            ]
          }),
        ]
      }),

      new Paragraph({ children: [new PageBreak()] }),

      // ===== 6. ВАЖНЫЕ АСПЕКТЫ =====
      heading(1, '6. \u0412\u0430\u0436\u043d\u044b\u0435 \u0430\u0441\u043f\u0435\u043a\u0442\u044b \u0438 \u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u044f'),

      heading(2, '6.1. \u0411\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c \u0438 \u043a\u043e\u043d\u0444\u0438\u0434\u0435\u043d\u0446\u0438\u0430\u043b\u044c\u043d\u043e\u0441\u0442\u044c'),
      p('\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u0431\u0430\u0437\u044b \u0437\u043d\u0430\u043d\u0438\u0439 \u043e\u0431\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u044e\u0442\u0441\u044f \u0447\u0435\u0440\u0435\u0437 \u043e\u0431\u043b\u0430\u0447\u043d\u044b\u0439 \u0441\u0435\u0440\u0432\u0438\u0441 RouterAI, \u0447\u0442\u043e \u043f\u0440\u0438\u0435\u043c\u043b\u0435\u043c\u043e \u0434\u043b\u044f \u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438, \u0442\u0430\u043a \u043a\u0430\u043a \u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u044f\u0432\u043b\u044f\u044e\u0442\u0441\u044f \u043f\u0443\u0431\u043b\u0438\u0447\u043d\u043e\u0439 \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u0435\u0439. \u041e\u0434\u043d\u0430\u043a\u043e \u043b\u0438\u0447\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432 \u041d\u0415 \u043f\u0435\u0440\u0435\u0434\u0430\u044e\u0442\u0441\u044f \u0432 \u043e\u0431\u043b\u0430\u043a\u043e \u2014 \u0441\u0438\u0441\u0442\u0435\u043c\u0430 \u043e\u0431\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u0435\u0442 \u0442\u043e\u043b\u044c\u043a\u043e \u0432\u043e\u043f\u0440\u043e\u0441\u044b \u0438 \u043a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 \u0434\u0438\u0430\u043b\u043e\u0433\u0430.'),
      p('\u2013 \u0410\u0443\u0442\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f \u0447\u0435\u0440\u0435\u0437 Supabase JWT', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 Row Level Security (RLS) \u0432 PostgreSQL', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041b\u0438\u0447\u043d\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432 \u043d\u0435 \u043f\u0435\u0440\u0435\u0434\u0430\u044e\u0442\u0441\u044f \u0432 LLM', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u2014 \u043f\u0443\u0431\u043b\u0438\u0447\u043d\u0430\u044f \u0438\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f', { numbering: { reference: 'bullets', level: 0 } }),

      heading(2, '6.2. \u0417\u0430\u0432\u0438\u0441\u0438\u043c\u043e\u0441\u0442\u044c \u043e\u0442 \u0432\u043d\u0435\u0448\u043d\u0438\u0445 \u0441\u0435\u0440\u0432\u0438\u0441\u043e\u0432'),
      p('\u0421\u0438\u0441\u0442\u0435\u043c\u0430 \u0437\u0430\u0432\u0438\u0441\u0438\u0442 \u043e\u0442 \u043e\u0431\u043b\u0430\u0447\u043d\u043e\u0433\u043e \u0441\u0435\u0440\u0432\u0438\u0441\u0430 RouterAI \u0434\u043b\u044f LLM-\u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432 \u0438 \u044d\u043c\u0431\u0435\u0434\u0434\u0438\u043d\u0433\u043e\u0432. \u041f\u0440\u0438 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0441\u0442\u0438 RouterAI \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u043e\u0442\u0432\u0435\u0442\u043e\u0432 \u043d\u0435\u0432\u043e\u0437\u043c\u043e\u0436\u043d\u0430.'),
      p('\u2013 RouterAI \u2014 \u0432\u043d\u0435\u0448\u043d\u0438\u0439 \u043f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440 LLM (Mercury 2, pplx-embed)', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041f\u0440\u0438 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0441\u0442\u0438 \u2014 fallback \u043d\u0430 \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440\u0430', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u043a\u044d\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432 (\u043f\u043b\u0430\u043d\u0438\u0440\u0443\u0435\u0442\u0441\u044f)', { numbering: { reference: 'bullets', level: 0 } }),

      heading(2, '6.3. \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0431\u0430\u0437\u044b \u0437\u043d\u0430\u043d\u0438\u0439'),
      p('\u0411\u0430\u0437\u0430 \u0437\u043d\u0430\u043d\u0438\u0439 \u0442\u0440\u0435\u0431\u0443\u0435\u0442 \u0440\u0443\u0447\u043d\u043e\u0433\u043e \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f \u043f\u0440\u0438 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0438 \u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0445 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432. \u041f\u0440\u043e\u0446\u0435\u0441\u0441 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f: \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043d\u043e\u0432\u044b\u0445 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u043e\u0432 \u2192 \u043f\u0430\u0440\u0441\u0438\u043d\u0433 \u2192 \u0444\u0440\u0430\u0433\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f \u2192 LLM-\u043e\u0431\u043e\u0433\u0430\u0449\u0435\u043d\u0438\u0435 \u2192 \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0432 Qdrant.'),

      heading(2, '6.4. Fallback \u043d\u0430 \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440\u0430'),
      p('\u0415\u0441\u043b\u0438 \u043e\u0442\u0432\u0435\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d \u0432 \u0431\u0430\u0437\u0435 \u0437\u043d\u0430\u043d\u0438\u0439 (\u043f\u043e\u0440\u043e\u0433 \u0440\u0435\u043b\u0435\u0432\u0430\u043d\u0442\u043d\u043e\u0441\u0442\u0438 \u043d\u0438\u0436\u0435 0,2), \u0441\u0438\u0441\u0442\u0435\u043c\u0430 \u043f\u0440\u0435\u0434\u043b\u0430\u0433\u0430\u0435\u0442 \u043f\u0435\u0440\u0435\u0432\u043e\u0434 \u043d\u0430 \u0436\u0438\u0432\u043e\u0433\u043e \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440\u0430. \u042d\u0442\u043e \u043a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0432\u0430\u0436\u043d\u043e \u0434\u043b\u044f \u0441\u043b\u0443\u0447\u0430\u0435\u0432, \u043a\u043e\u0433\u0434\u0430 \u0432\u043e\u043f\u0440\u043e\u0441 \u043a\u043b\u0438\u0435\u043d\u0442\u0430 \u0432\u044b\u0445\u043e\u0434\u0438\u0442 \u0437\u0430 \u0440\u0430\u043c\u043a\u0438 \u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u043e\u0439 \u0431\u0430\u0437\u044b.'),

      new Paragraph({ children: [new PageBreak()] }),

      // ===== 7. ПРЕИМУЩЕСТВА =====
      heading(1, '7. \u041f\u0440\u0435\u0438\u043c\u0443\u0449\u0435\u0441\u0442\u0432\u0430 \u0441\u0438\u0441\u0442\u0435\u043c\u044b'),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [500, 8526],
        rows: [
          new TableRow({
            children: [
              makeCell('\u2116', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
              makeCell('\u041f\u0440\u0435\u0438\u043c\u0443\u0449\u0435\u0441\u0442\u0432\u043e', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('1', { fill: 'F5F5F5', align: AlignmentType.CENTER }),
              makeCell('\u041d\u0438\u0437\u043a\u0438\u0435 \u0430\u043f\u043f\u0430\u0440\u0430\u0442\u043d\u044b\u0435 \u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f \u2014 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442 \u043d\u0430 VPS 4 vCPU / 4\u20138 \u0413\u0411 RAM', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('2'),
              makeCell('\u0418\u0418-\u0430\u0433\u0435\u043d\u0442\u044b \u0434\u043b\u044f \u0443\u043b\u0443\u0447\u0448\u0435\u043d\u0438\u044f \u043f\u043e\u0438\u0441\u043a\u0430 \u2014 \u043a\u043b\u0430\u0441\u0441\u0438\u0444\u0438\u043a\u0430\u0446\u0438\u044f, \u0434\u0435\u043a\u043e\u043c\u043f\u043e\u0437\u0438\u0446\u0438\u044f, \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430 \u0432\u0435\u0441\u043e\u0432'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('3', { fill: 'F5F5F5' }),
              makeCell('\u0413\u0438\u0431\u0440\u0438\u0434\u043d\u044b\u0439 \u043f\u043e\u0438\u0441\u043a \u043f\u043e 4 \u043a\u043e\u043c\u043f\u043e\u043d\u0435\u043d\u0442\u0430\u043c \u2014 3 \u0432\u0435\u043a\u0442\u043e\u0440\u0430 + BM25 \u0434\u043b\u044f \u043c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0439 \u0440\u0435\u043b\u0435\u0432\u0430\u043d\u0442\u043d\u043e\u0441\u0442\u0438', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('4'),
              makeCell('\u041e\u0431\u0440\u0430\u0442\u043d\u0430\u044f \u0441\u0432\u044f\u0437\u044c \u2014 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438 \u043e\u0446\u0435\u043d\u0438\u0432\u0430\u044e\u0442 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e \u043e\u0442\u0432\u0435\u0442\u043e\u0432'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('5', { fill: 'F5F5F5' }),
              makeCell('\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0439 \u2014 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u0434\u0438\u0430\u043b\u043e\u0433\u043e\u0432 \u0434\u043b\u044f \u0430\u043d\u0430\u043b\u0438\u0442\u0438\u043a\u0438 \u0438 \u043f\u043e\u0432\u0442\u043e\u0440\u043d\u043e\u0433\u043e \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('6'),
              makeCell('\u0413\u043e\u0440\u044f\u0447\u0438\u0435 \u043a\u043b\u0430\u0432\u0438\u0448\u0438 \u2014 \u0443\u0441\u043a\u043e\u0440\u0435\u043d\u0438\u0435 \u0440\u0430\u0431\u043e\u0442\u044b \u0434\u043b\u044f \u043e\u043f\u0435\u0440\u0430\u0442\u043e\u0440\u043e\u0432 (Ctrl+N, Ctrl+H, Ctrl+L...)'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('7', { fill: 'F5F5F5' }),
              makeCell('Streaming \u043e\u0442\u0432\u0435\u0442\u043e\u0432 (SSE) \u2014 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0432\u0438\u0434\u0438\u0442 \u043e\u0442\u0432\u0435\u0442 \u043f\u043e \u043c\u0435\u0440\u0435 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u0438', { fill: 'F5F5F5' }),
            ]
          }),
        ]
      }),

      // ===== 8. НЕДОСТАТКИ =====
      heading(1, '8. \u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043a\u0438 \u0438 \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u044f \u0440\u0430\u0437\u0432\u0438\u0442\u0438\u044f'),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [500, 8526],
        rows: [
          new TableRow({
            children: [
              makeCell('\u2116', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
              makeCell('\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043e\u043a / \u041d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435', { bold: true, fill: 'E0E0E0', align: AlignmentType.CENTER }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('1', { fill: 'F5F5F5', align: AlignmentType.CENTER }),
              makeCell('\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u043a\u044d\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f \u0437\u0430\u043f\u0440\u043e\u0441\u043e\u0432 \u2014 \u043f\u043e\u0432\u0442\u043e\u0440\u043d\u044b\u0435 \u0432\u043e\u043f\u0440\u043e\u0441\u044b \u043e\u0431\u0440\u0430\u0431\u0430\u0442\u044b\u0432\u0430\u044e\u0442\u0441\u044f \u0437\u0430\u043d\u043e\u0432\u043e', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('2'),
              makeCell('\u0417\u0430\u0432\u0438\u0441\u0438\u043c\u043e\u0441\u0442\u044c \u043e\u0442 RouterAI \u2014 \u043f\u0440\u0438 \u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u043e\u0441\u0442\u0438 \u0432\u043d\u0435\u0448\u043d\u0435\u0433\u043e \u0441\u0435\u0440\u0432\u0438\u0441\u0430 \u0433\u0435\u043d\u0435\u0440\u0430\u0446\u0438\u044f \u043d\u0435\u0432\u043e\u0437\u043c\u043e\u0436\u043d\u0430'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('3', { fill: 'F5F5F5' }),
              makeCell('\u0420\u0443\u0447\u043d\u043e\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0431\u0430\u0437\u044b \u0437\u043d\u0430\u043d\u0438\u0439 \u2014 \u043d\u0435\u0442 \u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u043e\u0433\u043e \u043c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433\u0430 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439 \u0432 \u043d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0445 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0445', { fill: 'F5F5F5' }),
            ]
          }),
          new TableRow({
            children: [
              makeCell('4'),
              makeCell('\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u043c\u0443\u043b\u044c\u0442\u0438\u044f\u0437\u044b\u0447\u043d\u043e\u0441\u0442\u0438 \u2014 \u0442\u043e\u043b\u044c\u043a\u043e \u0440\u0443\u0441\u0441\u043a\u0438\u0439 \u044f\u0437\u044b\u043a'),
            ]
          }),
          new TableRow({
            children: [
              makeCell('5', { fill: 'F5F5F5' }),
              makeCell('\u041d\u0435\u0442 \u0438\u043d\u0442\u0435\u0433\u0440\u0430\u0446\u0438\u0438 \u0441 CRM \u2014 \u0438\u0441\u0442\u043e\u0440\u0438\u044f \u0434\u0438\u0430\u043b\u043e\u0433\u043e\u0432 \u0445\u0440\u0430\u043d\u0438\u0442\u0441\u044f \u043e\u0442\u0434\u0435\u043b\u044c\u043d\u043e', { fill: 'F5F5F5' }),
            ]
          }),
        ]
      }),

      new Paragraph({ children: [new PageBreak()] }),

      // ===== 9. ТЕСТИРОВАНИЕ =====
      heading(1, '9. \u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b \u0442\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f'),
      p('\u0421\u0438\u0441\u0442\u0435\u043c\u0430 \u043f\u0440\u043e\u0442\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0430 \u0410\u043d\u043d\u043e\u0439 \u0411\u043e\u0440\u0438\u0441\u043e\u0432\u043d\u043e\u0439 \u2014 14 \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432 \u043f\u043e \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u0447\u0435\u0441\u043a\u043e\u043c\u0443 \u043f\u0440\u0438\u0441\u043e\u0435\u0434\u0438\u043d\u0435\u043d\u0438\u044e, 79 \u0437\u0430\u043c\u0435\u0447\u0430\u043d\u0438\u0439. \u0420\u0430\u0431\u043e\u0442\u0430 \u043d\u0430\u0434 \u043e\u0448\u0438\u0431\u043a\u0430\u043c\u0438 \u0432\u0435\u0434\u0451\u0442\u0441\u044f \u0434\u043b\u044f \u0432\u0442\u043e\u0440\u043e\u0439 \u0438\u0442\u0435\u0440\u0430\u0446\u0438\u0438 \u0442\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f.'),
      p('\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435 \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u0438 \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432:'),
      p('\u2013 \u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f (\u0442\u0430\u0440\u0438\u0444\u044b, \u0444\u043e\u0440\u043c\u0443\u043b\u044b \u0440\u0430\u0441\u0447\u0451\u0442\u0430)', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u044b\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b \u0434\u043b\u044f \u0437\u0430\u044f\u0432\u043a\u0438', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u0421\u0440\u043e\u043a\u0438 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041b\u044c\u0433\u043e\u0442\u044b \u0438 \u043e\u0441\u043e\u0431\u044b\u0435 \u0443\u0441\u043b\u043e\u0432\u0438\u044f', { numbering: { reference: 'bullets', level: 0 } }),
      p('\u2013 \u041f\u043e\u0448\u0430\u0433\u043e\u0432\u044b\u0435 \u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u0438 \u0434\u043b\u044f \u0440\u0430\u0437\u043b\u0438\u0447\u043d\u044b\u0445 \u0441\u0446\u0435\u043d\u0430\u0440\u0438\u0435\u0432', { numbering: { reference: 'bullets', level: 0 } }),

      // ===== 10. СХЕМА =====
      heading(1, '10. \u0421\u0445\u0435\u043c\u0430 \u0441\u0438\u0441\u0442\u0435\u043c\u044b'),
      p('\u041f\u043e\u043b\u043d\u0430\u044f \u0441\u0445\u0435\u043c\u0430 \u0430\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u044b \u0441\u0438\u0441\u0442\u0435\u043c\u044b \u043f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u0430 \u0432 \u0444\u0430\u0439\u043b\u0435 pipeline_data_preparation.drawio. \u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0432 draw.io \u0438\u043b\u0438 diagrams.net.'),

      new Paragraph({ spacing: { before: 400, after: 120 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: '\u2014 \u041a\u043e\u043d\u0435\u0446 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430 \u2014', size: 22, italics: true, font: 'Times New Roman' })] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('system_report.docx', buffer);
  console.log('Done: system_report.docx');
}).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
