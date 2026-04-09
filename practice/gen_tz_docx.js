const fs = require("fs");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  AlignmentType,
  BorderStyle,
  WidthType,
  ShadingType,
  LevelFormat,
  HeadingLevel,
  PageBreak,
  TabStopType,
  TabStopPosition,
} = require("docx");

// ============================================================
// Helpers
// ============================================================

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun(text)],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun(text)],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { line: 360, lineRule: "auto" },
    indent: opts.firstLine ? { firstLine: 709 } : undefined,
    alignment: opts.center ? AlignmentType.CENTER : undefined,
    children: [
      new TextRun({
        text,
        size: opts.size || 28,
        bold: opts.bold || false,
      }),
    ],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { line: 360, lineRule: "auto" },
    children: [new TextRun({ text, size: 28 })],
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { line: 360, lineRule: "auto" },
    children: [new TextRun({ text, size: 28 })],
  });
}

function emptyParagraphs(n = 1) {
  return Array(n)
    .fill(null)
    .map(
      () =>
        new Paragraph({
          spacing: { after: 300 },
          children: [],
        })
    );
}

function cell(text, opts = {}) {
  const border = {
    style: BorderStyle.SINGLE,
    size: 1,
    color: "CCCCCC",
  };
  const borders = opts.noBorder
    ? undefined
    : { top: border, bottom: border, left: border, right: border };

  return new TableCell({
    borders,
    width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
    shading: opts.shading
      ? { fill: opts.shading, type: ShadingType.CLEAR }
      : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [
      new Paragraph({
        alignment: opts.align || undefined,
        spacing: opts.spacing ? { after: opts.spacing } : undefined,
        children: [
          new TextRun({
            text,
            size: opts.size || 28,
            bold: opts.bold || false,
          }),
        ],
      }),
    ],
  });
}

// ============================================================
// Document content
// ============================================================

const children = [];

// --- Титульная страница: ЗАКАЗЧИК (правый верхний угол) ---
children.push(
  new Paragraph({
    indent: { left: 5664 },
    children: [new TextRun({ text: "ЗАКАЗЧИК", size: 28 })],
  })
);

children.push(
  new Paragraph({
    spacing: { after: 60 },
    indent: { left: 5664 },
    children: [
      new TextRun({
        text: "Заместитель Генерального директора —",
        size: 28,
      }),
      new TextRun({ text: "", break: 1 }),
      new TextRun({ text: "Директор ПО «ИТиС»", size: 24 }),
    ],
  })
);

children.push(
  new Paragraph({
    spacing: { after: 60 },
    indent: { left: 5664 },
    children: [new TextRun({ text: "________ / Р. Х. Хадыев", size: 28 })],
  })
);

children.push(
  new Paragraph({
    indent: { left: 5664 },
    children: [new TextRun({ text: "«___» _____________ 2026 г.", size: 28 })],
  })
);

children.push(...emptyParagraphs(3));

// --- ТЕХНИЧЕСКОЕ ЗАДАНИЕ (центр) ---
children.push(
  new Paragraph({
    spacing: { after: 80 },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({ text: "ТЕХНИЧЕСКОЕ ЗАДАНИЕ", size: 28, bold: true }),
    ],
  })
);

children.push(
  new Paragraph({
    spacing: { line: 360, lineRule: "auto" },
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "РАЗРАБОТКА ИНТЕЛЛЕКТУАЛЬНОГО АССИСТЕНТА НА ОСНОВЕ МЕТОДОВ ОБРАБОТКИ ЕСТЕСТВЕННОГО ЯЗЫКА ДЛЯ АВТОМАТИЗАЦИИ ТЕХНИЧЕСКОЙ ПОДДЕРЖКИ НУЛЕВОГО УРОВНЯ В МОДУЛЕ «1С: УЧЕТ ТЕХНОЛОГИЧЕСКОГО ПРИСОЕДИНЕНИЯ»",
        size: 28,
      }),
    ],
  })
);

children.push(...emptyParagraphs(4));

// --- Таблица СОГЛАСОВАНО / СОСТАВИЛ ---
const agreeW = 3163;
const spacerW = 2507;
const authorW = 3816;

children.push(
  new Table({
    width: { size: agreeW + spacerW + authorW, type: WidthType.DXA },
    columnWidths: [agreeW, spacerW, authorW],
    rows: [
      new TableRow({
        children: [
          // СОГЛАСОВАНО
          new TableCell({
            width: { size: agreeW, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 0, right: 150 },
            children: [
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "СОГЛАСОВАНО", size: 28, bold: true }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [new TextRun({ text: "доц., к.т.н. ", size: 28 })],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "В. М. Гиниятуллин", size: 28 }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "Подпись _____________", size: 28 }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "«___» __________2026 г.", size: 28 }),
                ],
              }),
            ],
          }),
          // spacer
          new TableCell({
            width: { size: spacerW, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 150, right: 150 },
            children: [new Paragraph({ children: [] })],
          }),
          // СОСТАВИЛ
          new TableCell({
            width: { size: authorW, type: WidthType.DXA },
            margins: { top: 80, bottom: 80, left: 150, right: 0 },
            children: [
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "СОСТАВИЛ", size: 28, bold: true }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({
                    text: "студент группы БПОи-22-04",
                    size: 28,
                  }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "А. Ф. Сабитов", size: 28 }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "Подпись _____________", size: 28 }),
                ],
              }),
              new Paragraph({
                spacing: { after: 60 },
                children: [
                  new TextRun({ text: "«___» ___________ 2026 г.", size: 28 }),
                ],
              }),
            ],
          }),
        ],
      }),
    ],
  })
);

children.push(...emptyParagraphs(2));

// --- Город и год ---
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "г. Уфа, 2026", size: 28 })],
  })
);

// Разрыв страницы после титульника
children.push(new Paragraph({ children: [new PageBreak()] }));

// ============================================================
// ОСНОВНОЕ СОДЕРЖИМОЕ
// ============================================================

// --- 1. Наименование программы ---
children.push(heading1("1. Наименование программы"));
children.push(
  body(
    "Программное средство «Интеллектуальный ассистент» для автоматизации консультационной поддержки по вопросам технологического присоединения к электрическим сетям ООО «Башкирэнерго».",
    { firstLine: true }
  )
);

// --- 2. Основание для разработки ---
children.push(heading1("2. Основание для разработки"));
children.push(
  body(
    "Разработка осуществляется в рамках выполнения выпускной квалификационной работы для автоматизации обработки обращений потребителей в ООО «Башкирэнерго» (адрес: 450008, Республика Башкортостан, г. Уфа, ул. Российская, д. 56; основной вид деятельности — передача и распределение электроэнергии; численность персонала — свыше 5 000 сотрудников; дата основания — 1995 год).",
    { firstLine: true }
  )
);

// --- 3. Область применения ---
children.push(heading1("3. Область применения программы"));
children.push(
  body(
    "Программное средство применяется в процессе оказания услуги «Технологическое присоединение» и предназначено для автоматизации консультационной поддержки потребителей через веб-интерфейс.",
    { firstLine: true }
  )
);

// --- 4. Цель разработки ---
children.push(heading1("4. Цель разработки"));
children.push(
  body(
    "Цель разработки — повышение эффективности консультационной поддержки потребителей услуги технологического присоединения за счёт:",
    { firstLine: true }
  )
);
children.push(
  numbered(
    "сокращения среднего времени обработки типового обращения с 8 минут до 2 минут;"
  )
);
children.push(
  numbered(
    "снижения нагрузки на операторов колл-центра на 40–60% путём автоматизации обработки стандартных запросов;"
  )
);
children.push(
  numbered(
    "повышения качества и юридической точности предоставляемой информации через централизованный семантический поиск по нормативным документам;"
  )
);
children.push(
  numbered(
    "обеспечения круглосуточной доступности консультационной поддержки без увеличения численности персонала."
  )
);

// --- 5. Целевая аудитория ---
children.push(heading1("5. Целевая аудитория"));
children.push(
  body("Физические лица, обращающиеся по вопросам подключения объектов к электросетям;", { firstLine: true })
);
children.push(
  body("Юридические лица и индивидуальные предприниматели;", { firstLine: true })
);
children.push(
  body("Операторы колл-центра ООО «Башкирэнерго»;", { firstLine: true })
);
children.push(
  body("Специалисты отдела технологического присоединения.", { firstLine: true })
);

// --- 6. Функциональные требования ---
children.push(heading1("6. Функциональные требования"));

children.push(heading2("6.1. Главный интерфейс"));
children.push(
  numbered("Отображение окна чата для ввода вопроса в свободной форме;")
);
children.push(
  numbered(
    "Кнопки быстрого доступа к часто задаваемым темам (стоимость, документы, сроки, льготы);"
  )
);
children.push(
  numbered("Раздел «Помощь» с инструкцией по использованию ассистента;")
);
children.push(
  numbered(
    "Отображение источников ответа с оценками релевантности (семантическое и лексическое сходство);"
  )
);
children.push(
  numbered(
    "Панель настройки параметров поиска (количество источников, температура генерации, порог релевантности);"
  )
);
children.push(
  numbered("Возможность переключения на оператора при нерелевантном ответе;")
);
children.push(
  numbered("Система обратной связи (оценка качества ответа пользователем).")
);

children.push(heading2("6.2. Обработка обращения"));
children.push(
  numbered(
    "Приём текста вопроса от пользователя на естественном русском языке;"
  )
);
children.push(
  numbered(
    "Автоматическое переформулирование запроса с учётом контекста диалога (агент Query Generator);"
  )
);
children.push(
  numbered(
    "Гибридный поиск по базе нормативных документов: комбинация семантического поиска по трём векторам (pref, hype, contextual) и лексического поиска BM25 (агент Search Agent);"
  )
);
children.push(
  numbered(
    "Генерация ответа с обязательными ссылками на источники в формате [1], [2] (агент Response Agent);"
  )
);
children.push(
  numbered(
    "Оценка уверенности системы в правильности ответа на основе релевантности найденных источников;"
  )
);
children.push(
  numbered(
    "При низкой уверенности или нерелевантности запроса — предложение уточнить вопрос или переключение на оператора."
  )
);

children.push(heading2("6.3. Работа с базой знаний"));
children.push(
  numbered(
    "Хранение обработанных документов в векторной базе данных Qdrant с тремя векторами на чанк;"
  )
);
children.push(
  numbered(
    "Автоматическое LLM-обогащение чанков: генерация краткого содержания (summary), гипотетических вопросов, ключевых слов и сущностей;"
  )
);
children.push(
  numbered(
    "Возможность обновления базы знаний путём повторной загрузки документов и переиндексации;"
  )
);
children.push(
  numbered(
    "Ведение журнала обращений и выданных ответов в базе данных Supabase PostgreSQL для последующего анализа."
  )
);

children.push(heading2("6.4. Общие функции"));
children.push(
  numbered(
    "Сохранение истории диалога в личном кабинете пользователя (сессии чатов);"
  )
);
children.push(
  numbered("Возможность возобновления предыдущих диалогов;")
);
children.push(
  numbered(
    "Формирование отчёта по обращению с указанием даты, времени, содержания и оценки;"
  )
);
children.push(
  numbered(
    "Адаптация интерфейса под разные устройства (компьютер, планшет, смартфон);"
  )
);
children.push(
  numbered(
    "Поддержка горячих клавиш для ускоренной работы (Ctrl+N — новый чат, Ctrl+H — история, Ctrl+L — фокус на ввод, Ctrl+S — источники, Ctrl+Shift+C — копировать ответ);"
  )
);
children.push(
  numbered(
    "Аутентификация и регистрация пользователей через Supabase Auth (JWT-токены);"
  )
);
children.push(
  numbered(
    "Поддержка русского языка как основного, с возможностью расширения на другие языки."
  )
);

// --- 7. Архитектура системы ---
children.push(heading1("7. Архитектура системы"));
children.push(
  body(
    "Система построена на основе мультиагентной архитектуры Agentic RAG (Retrieval-Augmented Generation) с гибридным поиском. Обработка запроса выполняется последовательно тремя специализированными агентами:",
    { firstLine: true }
  )
);

children.push(heading2("7.1. Агенты системы"));

// Таблица агентов
const agentTableW = 9360;
const agentCol1 = 2800;
const agentCol2 = 6560;

children.push(
  new Table({
    width: { size: agentTableW, type: WidthType.DXA },
    columnWidths: [agentCol1, agentCol2],
    rows: [
      new TableRow({
        children: [
          cell("Агент", { bold: true, size: 24, shading: "D5E8F0", width: agentCol1 }),
          cell("Назначение", { bold: true, size: 24, shading: "D5E8F0", width: agentCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Query Generator", { size: 24, width: agentCol1 }),
          cell(
            "Переформулирует запрос пользователя с учётом предыдущих сообщений в сессии, разбивает сложные вопросы на составные части для повышения точности поиска.",
            { size: 24, width: agentCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Search Agent", { size: 24, width: agentCol1 }),
          cell(
            "Выполняет гибридный поиск с настраиваемыми весами в зависимости от сложности запроса: 0.4×pref + 0.3×hype + 0.1×contextual + 0.2×BM25.",
            { size: 24, width: agentCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Response Agent", { size: 24, width: agentCol1 }),
          cell(
            "Генерирует финальный ответ на основе найденных источников с обязательными ссылками на документы. При отсутствии релевантных источников запрашивает уточнение или предлагает переключение на оператора.",
            { size: 24, width: agentCol2 }
          ),
        ],
      }),
    ],
  })
);

children.push(heading2("7.2. Стратегия векторного кодирования"));
children.push(
  body(
    "Каждый фрагмент документа (чанк) кодируется тремя векторами в базе Qdrant:",
    { firstLine: true }
  )
);

// Таблица векторов
const vecCol1 = 2000;
const vecCol2 = 3500;
const vecCol3 = 3860;

children.push(
  new Table({
    width: { size: agentTableW, type: WidthType.DXA },
    columnWidths: [vecCol1, vecCol2, vecCol3],
    rows: [
      new TableRow({
        children: [
          cell("Вектор", { bold: true, size: 24, shading: "D5E8F0", width: vecCol1 }),
          cell("Содержание", { bold: true, size: 24, shading: "D5E8F0", width: vecCol2 }),
          cell("Назначение", { bold: true, size: 24, shading: "D5E8F0", width: vecCol3 }),
        ],
      }),
      new TableRow({
        children: [
          cell("pref", { size: 24, width: vecCol1 }),
          cell("summary + content", { size: 24, width: vecCol2 }),
          cell(
            "Семантический поиск по краткому содержанию и тексту чанка",
            { size: 24, width: vecCol3 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("hype", { size: 24, width: vecCol1 }),
          cell("hypothetical questions", { size: 24, width: vecCol2 }),
          cell(
            "Поиск по гипотетическим вопросам, на которые чанк может ответить",
            { size: 24, width: vecCol3 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("contextual", { size: 24, width: vecCol1 }),
          cell("prev + current + next", { size: 24, width: vecCol2 }),
          cell(
            "Учёт контекста соседних фрагментов для повышения релевантности",
            { size: 24, width: vecCol3 }
          ),
        ],
      }),
    ],
  })
);

children.push(heading2("7.3. Компоненты системы"));
children.push(
  body("Система состоит из следующих модулей:", { firstLine: true })
);
children.push(
  numbered(
    "Веб-интерфейс (Vue.js 3, Vite, Pinia, Vue Router) — интерфейс для взаимодействия с клиентом;"
  )
);
children.push(
  numbered(
    "Модуль авторизации и регистрации (Supabase Auth) — JWT-аутентификация пользователей;"
  )
);
children.push(
  numbered(
    "Модуль ИИ и поиска (FastAPI + Uvicorn, мультиагентная архитектура) — обработка запросов, поиск, генерация ответов;"
  )
);
children.push(
  numbered(
    "База знаний (Qdrant) — векторное хранилище для семантического поиска;"
  )
);
children.push(
  numbered(
    "База данных пользователей и истории чатов (Supabase PostgreSQL) — хранение сессий, вопросов, ответов, обратной связи."
  )
);

// --- 8. Требования к интерфейсу ---
children.push(heading1("8. Требования к интерфейсу"));
children.push(
  numbered("Интерфейс на русском языке;")
);
children.push(
  numbered(
    "Единый стиль оформления в соответствии с корпоративными стандартами ООО «Башкирэнерго»;"
  )
);
children.push(
  numbered(
    "Чёткое разделение на блоки: ввод вопроса, отображение ответа, источники, дополнительные действия;"
  )
);
children.push(
  numbered(
    "Наличие визуальных подсказок и примеров формулировок вопросов;"
  )
);
children.push(
  numbered(
    "Адаптивный дизайн для корректного отображения на экранах разного размера;"
  )
);
children.push(
  numbered(
    "Анимация копирования ответа с визуальной обратной связью;"
  )
);
children.push(
  numbered(
    "Отображение оценок релевантности источников в процентах (семантическое и лексическое сходство)."
  )
);

// --- 9. Технические требования ---
children.push(heading1("9. Технические требования"));

children.push(heading2("9.1. Минимальные требования к серверу"));

const srvCol1 = 3500;
const srvCol2 = 5860;

children.push(
  new Table({
    width: { size: agentTableW, type: WidthType.DXA },
    columnWidths: [srvCol1, srvCol2],
    rows: [
      new TableRow({
        children: [
          cell("Ресурс", { bold: true, size: 24, shading: "D5E8F0", width: srvCol1 }),
          cell("Требование", { bold: true, size: 24, shading: "D5E8F0", width: srvCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Процессор", { size: 24, width: srvCol1 }),
          cell("4 ядра", { size: 24, width: srvCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Оперативная память", { size: 24, width: srvCol1 }),
          cell("4–8 ГБ", { size: 24, width: srvCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Дисковое пространство", { size: 24, width: srvCol1 }),
          cell("от 10 ГБ (зависит от объёма логов и базы чатов)", { size: 24, width: srvCol2 }),
        ],
      }),
    ],
  })
);

children.push(heading2("9.2. Стек технологий"));

const stackCol1 = 2800;
const stackCol2 = 6560;

children.push(
  new Table({
    width: { size: agentTableW, type: WidthType.DXA },
    columnWidths: [stackCol1, stackCol2],
    rows: [
      new TableRow({
        children: [
          cell("Компонент", { bold: true, size: 24, shading: "D5E8F0", width: stackCol1 }),
          cell("Технология", { bold: true, size: 24, shading: "D5E8F0", width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Backend", { size: 24, width: stackCol1 }),
          cell("Python 3.11+, FastAPI, Uvicorn", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Frontend", { size: 24, width: stackCol1 }),
          cell("Vue.js 3, Vite, Pinia, Vue Router", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Vector DB", { size: 24, width: stackCol1 }),
          cell("Qdrant", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("RDBMS + Auth", { size: 24, width: stackCol1 }),
          cell("Supabase (PostgreSQL + Auth)", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("LLM", { size: 24, width: stackCol1 }),
          cell("RouterAI (inception/mercury-2)", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Embeddings", { size: 24, width: stackCol1 }),
          cell("RouterAI (pplx-embed-v1-4b)", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Поиск", { size: 24, width: stackCol1 }),
          cell("rank-bm25, pymorphy3", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Контейнеризация", { size: 24, width: stackCol1 }),
          cell("Docker + Docker Compose", { size: 24, width: stackCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Reverse Proxy", { size: 24, width: stackCol1 }),
          cell("Nginx", { size: 24, width: stackCol2 }),
        ],
      }),
    ],
  })
);

children.push(heading2("9.3. Зависимость от внешних сервисов"));
children.push(
  body(
    "Система работает с платным сервисом RouterAI, который предоставляет доступ к языковой модели для генерации ответов (mercury-2) и эмбеддинг-модели для векторного поиска (pplx-embed-v1-4b). Запросы пользователей передаются в облако RouterAI, что создаёт риски для конфиденциальности персональных данных и требует отдельного рассмотрения.",
    { firstLine: true }
  )
);

children.push(heading2("9.4. Финансовые затраты"));
children.push(
  body(
    "Основные расходы — подписка на сервис RouterAI для доступа к языковым моделям. При нагрузке 100 запросов/день: ориентировочно 300–800 ₽/мес на AI модуль. Виртуальный сервер 4vCPU/8GB RAM: ~1 500–3 000 ₽/мес. Qdrant: от 0 ₽ (локально) до ~2 000 ₽/мес (cloud).",
    { firstLine: true }
  )
);

// --- 10. Преимущества и недостатки ---
children.push(heading1("10. Преимущества и недостатки"));

children.push(heading2("10.1. Недостатки (подлежащие исправлению)"));

const disCol1 = 3000;
const disCol2 = 6360;

children.push(
  new Table({
    width: { size: agentTableW, type: WidthType.DXA },
    columnWidths: [disCol1, disCol2],
    rows: [
      new TableRow({
        children: [
          cell("Недостаток", { bold: true, size: 24, shading: "D5E8F0", width: disCol1 }),
          cell("Описание", { bold: true, size: 24, shading: "D5E8F0", width: disCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Отсутствие кэширования", { size: 24, width: disCol1 }),
          cell(
            "На один и тот же вопрос модель отвечает заново, расходуя токены и время",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Риск некорректных ответов", { size: 24, width: disCol1 }),
          cell(
            "Если модель ответила неправильно, ответ сохраняется и показывается пользователям",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Необходимость работы с фидбеком", { size: 24, width: disCol1 }),
          cell(
            "Система сбора обратной связи реализована, но механизмы автоматического улучшения ещё не внедрены",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Зависимость от внешнего сервиса", { size: 24, width: disCol1 }),
          cell(
            "Данные запросов уходят в облако RouterAI — проблема безопасности и конфиденциальности",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Отсутствие автообновления базы знаний", { size: 24, width: disCol1 }),
          cell(
            "При обновлении нормативной базы документы нужно обновлять вручную",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Обновление только через программиста", { size: 24, width: disCol1 }),
          cell(
            "Нет интерфейса для самостоятельного обновления базы знаний",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
    ],
  })
);

children.push(heading2("10.2. Преимущества"));

children.push(
  new Table({
    width: { size: agentTableW, type: WidthType.DXA },
    columnWidths: [disCol1, disCol2],
    rows: [
      new TableRow({
        children: [
          cell("Преимущество", { bold: true, size: 24, shading: "D5E8F0", width: disCol1 }),
          cell("Описание", { bold: true, size: 24, shading: "D5E8F0", width: disCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Низкие требования к ресурсам", { size: 24, width: disCol1 }),
          cell(
            "Не требуется GPU для дообучения, система работает на CPU",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("ИИ-агенты", { size: 24, width: disCol1 }),
          cell(
            "Переформулирование запросов, разбиение сложных вопросов, адаптация параметров поиска",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Гибридный поиск", { size: 24, width: disCol1 }),
          cell(
            "Комбинация векторного поиска по трём векторам + BM25 с настраиваемыми весами",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Быстрое время ответа", { size: 24, width: disCol1 }),
          cell(
            "Благодаря диффузионной модели mercury-2 (>1000 токенов/сек)",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Система аналитики", { size: 24, width: disCol1 }),
          cell(
            "Запись всех чатов и пользователей для последующего анализа",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
      new TableRow({
        children: [
          cell("Обратная связь", { size: 24, width: disCol1 }),
          cell("Возможность оценки качества ответов клиентами", { size: 24, width: disCol2 }),
        ],
      }),
      new TableRow({
        children: [
          cell("Система уточнения", { size: 24, width: disCol1 }),
          cell(
            "Фильтрация нерелевантных запросов, fallback к оператору",
            { size: 24, width: disCol2 }
          ),
        ],
      }),
    ],
  })
);

// --- 11. Условия тиражирования ---
children.push(heading1("11. Условия тиражирования"));
children.push(
  body(
    "Для развёртывания системы на внутреннем контуре заказчика необходимо:",
    { firstLine: true }
  )
);
children.push(numbered("Предоставить сервер с указанными выше характеристиками;"));
children.push(numbered("Настроить Docker и Docker Compose;"));
children.push(numbered("Развернуть контейнеры из репозитория;"));
children.push(
  numbered("Настроить подключение к внутреннему Supabase (при необходимости);")
);
children.push(
  numbered(
    "При желании — заменить RouterAI на локальную языковую модель (требует GPU)."
  )
);
children.push(
  body(
    "Документация для развёртывания включена в репозиторий: README.md, QWEN.md, docker-compose.yml, .env.example.",
    { firstLine: true }
  )
);

// --- 12. Требования к документации ---
children.push(heading1("12. Требования к документации"));
children.push(
  numbered(
    "Руководство пользователя с пошаговыми примерами использования;"
  )
);
children.push(
  numbered(
    "Инструкция для администратора по установке, настройке и обновлению системы;"
  )
);
children.push(
  numbered(
    "Описание алгоритмов формирования ответов и работы с базой знаний;"
  )
);
children.push(
  numbered(
    "Отчёт о результатах тестирования с примерами типовых сценариев;"
  )
);
children.push(
  numbered(
    "Исходные материалы с комментариями для возможности дальнейшего сопровождения."
  )
);

// --- 13. Заключение ---
children.push(heading1("13. Заключение"));
children.push(
  body(
    "Разработанная система ИИ-ассистента для поддержки клиентов по вопросам технологического присоединения демонстрирует работоспособность подхода Agentic RAG с гибридным поиском. Система готова к тестированию и внедрению, при этом существует ряд направлений для улучшения: кэширование запросов, автоматическое обновление базы знаний, локализация языковых моделей для повышения безопасности данных.",
    { firstLine: true }
  )
);

// ============================================================
// Create document
// ============================================================

const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: "Times New Roman",
          size: 28,
        },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: {
          spacing: { before: 240, after: 240 },
          outlineLevel: 0,
        },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: {
          spacing: { before: 180, after: 180 },
          outlineLevel: 1,
        },
      },
      {
        id: "ListParagraph",
        name: "List Paragraph",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { font: "Times New Roman", size: 28 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 },
              },
            },
          },
        ],
      },
      {
        reference: "numbers",
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: "%1.",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 },
              },
            },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: {
            width: 11906,
            height: 16838,
          },
          margin: {
            top: 1134,
            right: 850,
            bottom: 1134,
            left: 1701,
          },
        },
      },
      children: children,
    },
  ],
});

// ============================================================
// Pack
// ============================================================

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("d:\\ai_assistant\\practice\\Техническое задание_новое.docx", buffer);
  console.log("Document created successfully!");
});
