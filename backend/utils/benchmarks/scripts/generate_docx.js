const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TableOfContents
} = require('docx');

const BODY = 24; // 12pt
const HEADING1 = 32; // 16pt
const HEADING2 = 28; // 14pt
const PAGE_W = 11906; // A4
const PAGE_H = 16838; // A4
const CONTENT_W = 9350; // A4 - 1" margins

const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

const BLUE = "2E75B6";
const LIGHT_BLUE = "D6E4F0";

function p(text, opts = {}) {
  const runs = [];
  if (typeof text === 'string') {
    runs.push(new TextRun({ text, size: opts.size || BODY, bold: opts.bold || false, font: "Arial" }));
  } else if (Array.isArray(text)) {
    text.forEach(t => runs.push(new TextRun({ text: t, size: opts.size || BODY, bold: opts.bold || false, font: "Arial" })));
  }
  return new Paragraph({
    ...opts.para || {},
    spacing: opts.spacing || { after: 120 },
    children: runs,
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, size: HEADING1, bold: true, font: "Arial", color: "1F4E79" })],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, size: HEADING2, bold: true, font: "Arial", color: "2E75B6" })],
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: BLUE, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({ text, size: 22, bold: true, font: "Arial", color: "FFFFFF" })],
    })],
  });
}

function cell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({ text: String(text), size: 20, font: "Arial", bold: opts.bold || false })],
    })],
  });
}

function makeTable(headers, rows, colWidths) {
  const tableRows = [
    new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) }),
    ...rows.map((row, ri) =>
      new TableRow({
        children: row.map((c, ci) => cell(c, colWidths[ci], {
          fill: ri % 2 === 0 ? "FFFFFF" : LIGHT_BLUE,
          bold: ci === 0 && headers.length > 3,
        })),
      })
    ),
  ];
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: tableRows,
  });
}

const children = [];

// ── TITLE PAGE ──
children.push(new Paragraph({ spacing: { before: 3000 }, children: [] }));
children.push(p("Benchmark Analysis Report", { size: 52, bold: true, spacing: { after: 240 }, para: { alignment: AlignmentType.CENTER } }));
children.push(p("AI Assistant (Башкирэнерго)", { size: 36, bold: true, spacing: { after: 480 }, para: { alignment: AlignmentType.CENTER } }));
children.push(new Paragraph({
  spacing: { after: 120 },
  alignment: AlignmentType.CENTER,
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 8 } },
  children: [],
}));
children.push(p("308 questions evaluated | 39.0% correct | Judge agreement 92.9%", { size: 24, spacing: { after: 240 }, para: { alignment: AlignmentType.CENTER } }));
children.push(p("Date: 2026-04-28", { size: 22, spacing: { after: 120 }, para: { alignment: AlignmentType.CENTER } }));
children.push(p("Review method: Judge LLM (deepseek-v3.2) + manual semantic verification", { size: 20, para: { alignment: AlignmentType.CENTER } }));

// ── PAGE BREAK + TOC ──
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading1("Table of Contents"));
children.push(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// ── 1. EXECUTIVE SUMMARY ──
children.push(heading1("1. Executive Summary"));
children.push(p("This report presents the results of benchmarking the AI Assistant for Bashkirenergo's technical connection support. 308 questions across three domain categories were evaluated using a judge LLM (deepseek-v3.2) supplemented by manual semantic verification."));
children.push(p(""));
children.push(p("Key metrics:", { bold: true }));
children.push(p(`   • Total questions: 308`));
children.push(p(`   • Correct answers: 120 (39.0%)`));
children.push(p(`   • Errors: 188 (61.0%)`));
children.push(p(`   • Judge-model agreement: 286/308 (92.9%)`));
children.push(p(`   • Answer not found in sources: 11 cases`));
children.push(p(`   • Average judge overall score: 3.71 / 10`));
children.push(p(""));

children.push(heading2("1.1 Category Breakdown"));
children.push(p(""));
children.push(makeTable(
  ["Category", "Questions", "Correct", "% Correct", "Avg Score"],
  [
    ["Личный кабинет (ЛК)", "53", "29", "54.7%", "4.17"],
    ["Дополнительные услуги (ДУ)", "67", "22", "32.8%", "3.51"],
    ["Технологическое присоединение (ТПП)", "188", "69", "36.7%", "3.65"],
    ["ВСЕГО", "308", "120", "39.0%", "3.71"],
  ],
  [2200, 1200, 1200, 1400, 1400]
));
children.push(p(""));
children.push(p(`The worst-performing category is ДУ (Additional Services) at 32.8% accuracy. The model frequently confuses ДУ procedures with ТП procedures, leading to incorrect recommendations.`));
children.push(p(`ЛК (Personal Account) performs best at 54.7%, suggesting the model has better grounding in the most common customer questions.`));

// ── 2. ERROR PATTERNS ──
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading1("2. Error Pattern Analysis"));
children.push(p("Classification of errors according to Anna Borisovna's review notes from expert evaluation:"));

children.push(heading2("2.1 Error Pattern Distribution"));
children.push(p(""));
children.push(makeTable(
  ["Error Pattern", "Occurrences", "% of Errors"],
  [
    ["Неверная терминология (\"обычный заявитель\", \"сетевой орган\")", "69", "36.7%"],
    ["Неверный расчёт стоимости или тарифы", "43", "22.9%"],
    ["Не учтены ограничения по мощности / категории заявителя", "41", "21.8%"],
    ["Льготная ставка / соц.льгота применяется некорректно", "22", "11.7%"],
    ["Путаница между ДУ и ТП", "6", "3.2%"],
  ],
  [5000, 1800, 1700]
));
children.push(p(""));
children.push(p("Key observations:", { bold: true }));
children.push(p("   • Terminology errors are the most common — model uses incorrect business vocabulary like \"обычный заявитель\" (should be ФЛ/ИП/ЮЛ) and \"сетевой орган\" (should be сетевая организация)"));
children.push(p("   • Cost calculation errors affect 22.9% of all errors — model provides wrong amounts, formulas, or tariff rates"));
children.push(p("   • Power/constraint errors (21.8%) — model fails to distinguish between ФЛ ≤ 15 kW, ИП/ЮЛ ≤ 150 kW, and свыше 150 kW categories"));

// ── 3. JUDGE ANALYSIS ──
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading1("3. Judge LLM Objectivity Analysis"));
children.push(p("The benchmark uses deepseek-v3.2 as a judge model to evaluate answer quality across 10 criteria."));
children.push(p(""));
children.push(makeTable(
  ["Metric", "Value"],
  [
    ["Total questions evaluated", "308"],
    ["Judge agrees with manual review", "286 (92.9%)"],
    ["Judge too strict (correct → wrong)", "5 (1.6%)"],
    ["Judge too lenient (wrong → correct)", "0 (0%)"],
    ["No judge data available", "17 (5.5%)"],
  ],
  [5000, 4350]
));
children.push(p(""));
children.push(p("The judge LLM demonstrates high reliability (92.9% agreement). No cases of leniency were found — the judge never passed an incorrect answer as correct. All 5 disagreement cases were the judge being too strict, penalizing verbose-but-substantively-correct answers."));
children.push(p(""));
children.push(p("Verdict: The judge model is fit for purpose. It can be used for automated benchmark evaluation with high confidence.", { bold: true }));

// ── 4. ROADMAP ──
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading1("4. Development Roadmap"));

children.push(heading2("4.1 Immediate Actions (Week 1-2)"));
children.push(p("1. Fix ДУ category accuracy (currently 32.8%)"));
children.push(p("   The model confuses ДУ (Additional Services) procedures with ТП (Technical Connection). Create separate system prompt for ДУ questions with explicit procedural boundaries."));
children.push(p("2. Improve search quality for deadlines and costs"));
children.push(p("   Model frequently gives wrong numerical answers. Add structured data tables to the vector database for cost amounts, deadlines, and tariff rates."));
children.push(p("3. Fix password recovery procedures"));
children.push(p("   Model applies generic password recovery to all cases, ignoring critical context differences (ЦОК registration, ЮЛ status, first-time vs returning user)."));

children.push(heading2("4.2 Short-term (Week 3-4)"));
children.push(p("1. Incorporate Anna Borisovna's expert corrections into system prompts"));
children.push(p("2. Improve source attribution — model says answer not found 11 times where it exists in sources"));
children.push(p("3. Add explicit power/category constraint rules to response agent (ФЛ ≤ 15 kW, ИП/ЮЛ ≤ 150 kW)"));

children.push(heading2("4.3 Medium-term (Month 2-3)"));
children.push(p("1. Separate response agents per domain category (ЛК / ДУ / ТПП)"));
children.push(p("2. Implement RAG quality monitoring — track context_recall scores, alert on degradation"));
children.push(p("3. Automate weekly benchmark runs with accuracy trend tracking"));
children.push(p("4. Expand benchmark dataset with more ДУ-specific and edge case questions"));
children.push(p("5. Reduce terminology errors through domain-specific fine-tuning or constrained vocabulary"));

// ── BUILD ──
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Arial", size: BODY },
      },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: 1100, right: 1280, bottom: 1100, left: 1280 },
      },
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            alignment: AlignmentType.RIGHT,
            spacing: { after: 60 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE, space: 4 } },
            children: [
              new TextRun({ text: "Башкирэнерго — AI Assistant Benchmark Report", size: 18, font: "Arial", color: "888888" }),
            ],
          }),
        ],
      }),
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "Page ", size: 18, font: "Arial", color: "888888" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: "888888" }),
            ],
          }),
        ],
      }),
    },
    children,
  }],
});

const outPath = "D:/ai_assistant/benchmark_report.docx";
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outPath, buffer);
  console.log("DOCX written to " + outPath);
  console.log("Size: " + (buffer.length / 1024).toFixed(1) + " KB");
});
