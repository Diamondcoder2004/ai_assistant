const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, HeadingLevel,
        BorderStyle, WidthType, ShadingType, PageNumber } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })] })]
  });
}

function cell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun(text)] })]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 280, after: 180 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          children: [new TextRun({ text: "AI-ассистент Башкирэнерго — Отчёт о проекте", color: "666666", size: 20 })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Страница ", size: 20 }), new TextRun({ children: [PageNumber.CURRENT], size: 20 })]
        })]
      })
    },
    children: [
      // Title
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("AI-ассистент для Башкирэнерго")]
      }),
      new Paragraph({
        spacing: { after: 360 },
        children: [new TextRun({ text: "Проект D:\\ai_assistant\\ai_assistant", italics: true, color: "666666" })]
      }),

      // 1. Название и цель проекта
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1. Название и цель проекта")] }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun("RAG-чат-бот для поддержки технологического присоединения к электросетям (ТПП) в компании Башкирэнерго.")]
      }),
      new Paragraph({
        spacing: { after: 240 },
        children: [new TextRun({ text: "Цель: ", bold: true }), new TextRun("Автоматизация ответов на вопросы клиентов по трём направлениям:")]
      }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "ЛК", bold: true }), new TextRun(" — Личный кабинет (операции с лицевым счётом)")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, children: [new TextRun({ text: "ДУ", bold: true }), new TextRun(" — Дополнительные услуги (платные сервисы)")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 }, spacing: { after: 240 }, children: [new TextRun({ text: "ТПП", bold: true }), new TextRun(" — Технологическое присоединение (основной процесс)")] }),

      // 2. Архитектура
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2. Архитектура")] }),
      new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("2.1 Компоненты системы")] }),

      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3000, 6026],
        rows: [
          new TableRow({ children: [headerCell("Компонент", 3000), headerCell("Описание", 6026)] }),
          new TableRow({ children: [cell("Vue 3 SPA", 3000), cell("Фронтенд на Vue 3 + Vite + Pinia + Tailwind", 6026)] }),
          new TableRow({ children: [cell("nginx :80", 3000), cell("Обслуживание статических файлов фронтенда", 6026)] }),
          new TableRow({ children: [cell("nginx :8877", 3000), cell("Проксирование API-запросов к бэкенду", 6026)] }),
          new TableRow({ children: [cell("FastAPI :8880", 3000), cell("Бэкенд-сервер (agents, tools, prompts)", 6026)] }),
          new TableRow({ children: [cell("Qdrant :6333", 3000), cell("Векторная база данных (коллекция BASHKIR_ENERGO_PERPLEXITY)", 6026)] }),
          new TableRow({ children: [cell("Supabase :8000", 3000), cell("JWT-авторизация + PostgreSQL (история чата)", 6026)] }),
          new TableRow({ children: [cell("RouterAI API", 3000), cell("LLM (inception/mercury-2) + embeddings (pplx-embed-v1-4b)", 6026)] }),
        ]
      }),

      new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 240 }, children: [new TextRun("2.2 Пайплайн агентов")] }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun("User Query → SearchAgent → Hybrid Search (Qdrant + BM25) → ResponseAgent → LLM Response + Sources")]
      }),

      new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 240 }, children: [new TextRun("2.3 Hybrid Search")] }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun("Четыре компонента поиска с весами (сумма = 1.0):")]
      }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "PREF", bold: true }), new TextRun(" — 0.4 (предпочтения пользователя)")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "HYPE", bold: true }), new TextRun(" — 0.3 (гипербола)")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "LEXICAL", bold: true }), new TextRun(" — 0.2 (лейкемия)")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 240 }, children: [new TextRun({ text: "CONTEXTUAL", bold: true }), new TextRun(" — 0.1 (контекст)")] }),

      // 3. Стек технологий
      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3. Стек технологий")] }),

      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2500, 6526],
        rows: [
          new TableRow({ children: [headerCell("Слой", 2500), headerCell("Технологии", 6526)] }),
          new TableRow({ children: [cell("Backend", 2500), cell("Python 3.11+, FastAPI (api.api:app)", 6526)] }),
          new TableRow({ children: [cell("Frontend", 2500), cell("Vue 3, Vite, Pinia, Tailwind", 6526)] }),
          new TableRow({ children: [cell("Database", 2500), cell("Supabase (PostgreSQL)", 6526)] }),
          new TableRow({ children: [cell("Vector DB", 2500), cell("Qdrant (port 6333)", 6526)] }),
          new TableRow({ children: [cell("LLM", 2500), cell("RouterAI: inception/mercury-2", 6526)] }),
          new TableRow({ children: [cell("Embeddings", 2500), cell("perplexity/pplx-embed-v1-4b", 6526)] }),
          new TableRow({ children: [cell("Judge", 2500), cell("deepseek/deepseek-v3.2", 6526)] }),
        ]
      }),

      // 4. Ключевые директории
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 360 }, children: [new TextRun("4. Ключевые директории")] }),

      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3000, 6026],
        rows: [
          new TableRow({ children: [headerCell("Директория", 3000), headerCell("Назначение", 6026)] }),
          new TableRow({ children: [cell("backend/", 3000), cell("FastAPI-приложение — agents, tools, prompts, config", 6026)] }),
          new TableRow({ children: [cell("backend/agents/", 3000), cell("SearchAgent, ResponseAgent, QueryGenerator", 6026)] }),
          new TableRow({ children: [cell("backend/api/", 3000), cell("REST endpoints: /query, /query/stream, /history, /feedback", 6026)] }),
          new TableRow({ children: [cell("backend/prompts/", 3000), cell("Системные промпты (ЗАБЛОКИРОВАНЫ — не менять стиль)", 6026)] }),
          new TableRow({ children: [cell("frontend/", 3000), cell("Vue 3 SPA — чат-интерфейс, история, профиль", 6026)] }),
          new TableRow({ children: [cell("api_benchmarks/", 3000), cell("CSV с результатами бенчмарков (оценки judge)", 6026)] }),
          new TableRow({ children: [cell("new_data/", 3000), cell("Датасеты бенчмарков: вопрос + ожидаемый ответ + source", 6026)] }),
          new TableRow({ children: [cell("practice/", 3000), cell("Тестовые документы и экспертные ревью (.docx)", 6026)] }),
          new TableRow({ children: [cell("docs/specs/", 3000), cell("Долговечные спецификации проекта", 6026)] }),
          new TableRow({ children: [cell(".opencode/", 3000), cell("OpenCode-слой: agents, skills", 6026)] }),
          new TableRow({ children: [cell("scripts/", 3000), cell("Утилиты (конвертация PDF, генерация слайдов)", 6026)] }),
        ]
      }),

      // 5. Конвенции и ограничения
      new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 360 }, children: [new TextRun("5. Конвенции и ограничения")] }),

      new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("5.1 Критические ограничения")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "Точка входа бэкенда:", bold: true }), new TextRun(" api.api:app (НЕ main.py)")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "BM25 нормализация:", bold: true }), new TextRun(" score / max_score (классическая, без tanh/softmax)")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "Промпты:", bold: true }), new TextRun(" заморожены в backend/prompts/ — не менять стиль написания")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun({ text: "Кодировка:", bold: true }), new TextRun(" UTF-8 для кириллицы; CSV с BOM (utf-8-sig)")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 240 }, children: [new TextRun({ text: "Supabase:", bold: true }), new TextRun(" двойная роль — JWT auth + хранилище истории чата")] }),

      new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("5.2 Конфигурация")] }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun("Для запуска: скопировать .env.example → .env и заполнить:")]
      }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("ROUTERAI_API_KEY")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("SUPABASE_URL")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, children: [new TextRun("SUPABASE_SERVICE_ROLE_KEY")] }),
      new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 240 }, children: [new TextRun("SUPABASE_JWT_SECRET")] }),

      new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("5.3 Команды")] }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: "Docker:", bold: true, break: 0 }), new TextRun(" docker-compose up -d --build / docker-compose down")]
      }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: "Backend локально:", bold: true, break: 0 }), new TextRun(" cd backend && uvicorn api.api:app --reload --host 0.0.0.0 --port 8880")]
      }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: "Frontend локально:", bold: true, break: 0 }), new TextRun(" cd frontend && npm run dev")]
      }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: "Тесты бэкенда:", bold: true, break: 0 }), new TextRun(" cd backend && pytest")]
      }),
      new Paragraph({
        spacing: { after: 360 },
        children: [new TextRun({ text: "Тесты фронтенда:", bold: true, break: 0 }), new TextRun(" cd frontend && npm run test:unit && npm run lint")]
      }),

      // Domain categories
      new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun("5.4 Доменные категории")] }),
      new Paragraph({
        spacing: { after: 120 },
        children: [
          new TextRun({ text: "ФЛ", bold: true }),
          new TextRun(" — Физическое лицо | "),
          new TextRun({ text: "ИП", bold: true }),
          new TextRun(" — Индивидуальный предприниматель | "),
          new TextRun({ text: "ЮЛ", bold: true }),
          new TextRun(" — Юридическое лицо")
        ]
      }),
      new Paragraph({
        spacing: { after: 120 },
        children: [new TextRun({ text: "Критерии оценки judge:", bold: true }), new TextRun(" relevance, completeness, helpfulness, clarity, hallucination_risk, context_recall, faithfulness, currency, binary_correctness, overall_score")]
      }),

      // Success definition
      new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 240 }, children: [new TextRun("5.5 Определение успеха")] }),
      new Paragraph({
        spacing: { after: 360 },
        children: [new TextRun("Корректный ответ = ответ модели совпадает с ожидаемой процедурой + правильная терминология + соблюдение доменных ограничений (категории ФЛ/ИП/ЮЛ, лимиты мощности, классы напряжения) + отсутствие галлюцинаций.")]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("D:/ai_assistant/practice/project_report.docx", buffer);
  console.log("Created: D:/ai_assistant/practice/project_report.docx");
});