const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat,
        TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageBreak, PageNumber } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, opts = {}) {
  return new TableCell({
    borders,
    width: opts.width ? { size: opts.width, type: WidthType.DXA } : undefined,
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: opts.bold || false, size: opts.size || 22 })] })]
  });
}

function p(text, opts = {}) {
  if (opts.heading) {
    return new Paragraph({
      heading: opts.heading,
      children: [new TextRun({ text, bold: true })],
      spacing: opts.spacing
    });
  }
  return new Paragraph({
    children: [new TextRun({ text, bold: opts.bold || false, size: opts.size || 22, italics: opts.italics || false })],
    spacing: opts.spacing,
    indent: opts.indent,
    alignment: opts.alignment
  });
}

function tableRow(cells, isHeader) {
  return new TableRow({
    children: cells.map(c => {
      if (typeof c === 'string') return cell(c, { bold: isHeader, shading: isHeader ? 'D5E8F0' : undefined });
      return cell(c.text, { ...c, shading: isHeader ? 'D5E8F0' : c.shading });
    })
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 24 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: 'Arial', color: '1F3864' },
        paragraph: { spacing: { before: 300, after: 200 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 28, bold: true, font: 'Arial', color: '2E75B6' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: '2E75B6' },
        paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: 'bullets',
        levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT,
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
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: 'Отчёт о проекте', size: 18, color: '666666', italics: true })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: 'Страница ', size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 })]
        })]
      })
    },
    children: [
      p('', { spacing: { after: 200 } }),
      p('ИИ-ассистент для поддержки клиентов по вопросам технологического присоединения', { heading: HeadingLevel.HEADING_1 }),
      p('БашкирЭнерго', { heading: HeadingLevel.HEADING_1 }),
      p('', { spacing: { after: 300 } }),

      p('Содержание', { heading: HeadingLevel.HEADING_1 }),
      new TableOfContents('Содержание', { hyperlink: true, headingStyleRange: '1-3' }),
      new Paragraph({ children: [new PageBreak()] }),

      // 1
      p('1. Постановка задачи', { heading: HeadingLevel.HEADING_1 }),
      p('Разработка интеллектуальной системы поддержки клиентов компании «БашкирЭнерго» по вопросам технологического присоединения. Система должна автоматически отвечать на вопросы клиентов, используя базу знаний нормативных документов, и предоставлять ответы в режиме реального времени через веб-интерфейс.'),
      p('Ключевые требования:', { bold: true }),
      p('Автоматизация ответов на типовые вопросы по технологическому присоединению', { numbering: { reference: 'bullets', level: 0 } }),
      p('Снижение нагрузки на операторов колл-центра', { numbering: { reference: 'bullets', level: 0 } }),
      p('Круглосуточная доступность', { numbering: { reference: 'bullets', level: 0 } }),
      p('Фиксация истории обращений и обратной связи для аналитики', { numbering: { reference: 'bullets', level: 0 } }),

      // 2
      p('2. Выбор архитектуры и подхода к решению', { heading: HeadingLevel.HEADING_1 }),
      p('2.1. Почему RAG, а не дообучение модели', { heading: HeadingLevel.HEADING_2 }),
      p('В качестве основного подхода была выбрана архитектура RAG (Retrieval-Augmented Generation) — генерация с извлечением из базы знаний. Причины:'),
      p('Отсутствие вычислительных ресурсов для дообучения (fine-tuning) языковой модели', { numbering: { reference: 'bullets', level: 0 } }),
      p('Актуальность знаний: нормативная база обновляется, и RAG позволяет обновлять ответы без переобучения модели', { numbering: { reference: 'bullets', level: 0 } }),
      p('Объяснимость: каждый ответ подкреплён конкретными источниками', { numbering: { reference: 'bullets', level: 0 } }),
      p('Контроль галлюцинаций: модель ограничена предоставленными документами', { numbering: { reference: 'bullets', level: 0 } }),

      p('2.2. Обзор рынка и анализ подходов', { heading: HeadingLevel.HEADING_2 }),
      p('При выборе архитектуры был проведён анализ существующих решений:'),
      p('Готовые RAG-чатботы (LangChain, LlamaIndex) — базовый функционал, но без учёта специфики домена', { numbering: { reference: 'bullets', level: 0 } }),
      p('Agentic RAG — несколько специализированных агентов для переформулирования запроса, поиска и генерации ответа', { numbering: { reference: 'bullets', level: 0 } }),
      p('Hybrid Search — комбинация векторного и лексического поиска (BM25)', { numbering: { reference: 'bullets', level: 0 } }),
      p('Без реранкера — отказ от отдельного этапа реранкинга в пользу гибридного скоринга с весами', { numbering: { reference: 'bullets', level: 0 } }),

      // 3
      p('3. Выбор языковых моделей', { heading: HeadingLevel.HEADING_1 }),
      p('3.1. Критерии выбора', { heading: HeadingLevel.HEADING_2 }),
      p('Скорость работы — время ответа должно быть приемлемым для пользователя', { numbering: { reference: 'bullets', level: 0 } }),
      p('Стоимость — использование платного сервиса RouterAI', { numbering: { reference: 'bullets', level: 0 } }),
      p('Качество генерации и эмбеддингов', { numbering: { reference: 'bullets', level: 0 } }),

      p('3.2. Выбранные модели', { heading: HeadingLevel.HEADING_2 }),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2700, 2700, 3626],
        rows: [
          tableRow([{ text: 'Компонент', bold: true }, { text: 'Модель', bold: true }, { text: 'Назначение', bold: true }], true),
          tableRow(['Генератор (LLM)', 'inception/mercury-2', 'Генерация ответов, переформулирование запросов']),
          tableRow(['Эмбеддинг-модель', 'pplx-embed-v1-4b', 'Векторное кодирование чанков и запросов']),
        ]
      }),
      p('Mercury 2 — диффузионная языковая модель, обеспечивающая высокую скорость генерации. Несмотря на 3–4 вызова LLM на один запрос, общее время ответа остаётся приемлемым.'),
      p('Метод выбора эмбеддинг-модели основывался на тестировании через top-k accuracy с использованием скрипта автоматизированного тестирования.'),

      // 4
      p('4. Архитектура системы', { heading: HeadingLevel.HEADING_1 }),
      p('4.1. Компоненты системы', { heading: HeadingLevel.HEADING_2 }),
      p('Веб-интерфейс (Vue.js 3) — интерфейс для взаимодействия с клиентом', { numbering: { reference: 'bullets', level: 0 } }),
      p('Модуль авторизации и регистрации (Supabase Auth) — JWT-аутентификация', { numbering: { reference: 'bullets', level: 0 } }),
      p('Модуль ИИ и поиска (FastAPI + агенты) — обработка запросов, поиск, генерация', { numbering: { reference: 'bullets', level: 0 } }),
      p('База знаний (Qdrant) — векторное хранилище для семантического поиска', { numbering: { reference: 'bullets', level: 0 } }),
      p('База данных пользователей и истории чатов (Supabase PostgreSQL)', { numbering: { reference: 'bullets', level: 0 } }),

      p('4.2. Зависимость от внешнего сервиса', { heading: HeadingLevel.HEADING_2 }),
      p('Система работает с платным сервисом RouterAI, который предоставляет доступ к языковым моделям. Запросы пользователей передаются в облако RouterAI, что создаёт риски для конфиденциальности персональных данных.'),

      // 5
      p('5. Формирование базы знаний', { heading: HeadingLevel.HEADING_1 }),
      p('5.1. Стратегия фрагментации (Chunking)', { heading: HeadingLevel.HEADING_2 }),
      p('Разбиение по заголовкам с рекурсивным дроблением крупных секций', { numbering: { reference: 'bullets', level: 0 } }),
      p('LLM-обогащение: генерация summary, гипотетических вопросов, ключевых слов', { numbering: { reference: 'bullets', level: 0 } }),
      p('Валидация и восстановление JSON при ошибках парсинга', { numbering: { reference: 'bullets', level: 0 } }),

      p('5.2. Стратегия кодирования (3 вектора на чанк)', { heading: HeadingLevel.HEADING_2 }),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2000, 3000, 4026],
        rows: [
          tableRow([{ text: 'Вектор', bold: true }, { text: 'Содержание', bold: true }, { text: 'Назначение', bold: true }], true),
          tableRow(['pref', 'summary + content', 'Семантический поиск по краткому содержанию']),
          tableRow(['hype', 'hypothetical questions', 'Поиск по гипотетическим вопросам']),
          tableRow(['contextual', 'prev + current + next чанк', 'Учёт контекста соседних фрагментов']),
        ]
      }),

      // 6
      p('6. Детали поиска и генерации: агенты', { heading: HeadingLevel.HEADING_1 }),
      p('6.1. Мультиагентная архитектура', { heading: HeadingLevel.HEADING_2 }),
      p('Query Generator — переформулирует запрос с учётом предыдущих сообщений', { numbering: { reference: 'bullets', level: 0 } }),
      p('Search Agent — выполняет гибридный поиск с настраиваемыми весами', { numbering: { reference: 'bullets', level: 0 } }),
      p('Response Agent — генерирует финальный ответ на основе источников', { numbering: { reference: 'bullets', level: 0 } }),

      p('6.2. Гибридный поиск', { heading: HeadingLevel.HEADING_2 }),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [2500, 1000, 5526],
        rows: [
          tableRow([{ text: 'Компонент', bold: true }, { text: 'Вес', bold: true }, { text: 'Описание', bold: true }], true),
          tableRow(['Семантический (pref)', '0.4', 'Поиск по вектору summary+content']),
          tableRow(['Семантический (hype)', '0.3', 'Поиск по вектору гипотетических вопросов']),
          tableRow(['Семантический (contextual)', '0.1', 'Поиск по вектору соседних чанков']),
          tableRow(['Лексический (BM25)', '0.2', 'Поиск по словесному совпадению']),
        ]
      }),
      p('', { spacing: { after: 60 } }),
      p('Формула: hybrid = 0,4×pref + 0,3×hype + 0,1×contextual + 0,2×bm25', { italics: true }),

      p('6.3. Система уточнения вопросов', { heading: HeadingLevel.HEADING_2 }),
      p('Если вопрос не относится к технологическому присоединению, система запрашивает уточнение. При отсутствии релевантных источников предусмотрен fallback к оператору.'),

      // 7
      p('7. Функциональные возможности', { heading: HeadingLevel.HEADING_1 }),
      p('История сообщений — сохранение всех вопросов и ответов', { numbering: { reference: 'bullets', level: 0 } }),
      p('Возобновление предыдущих диалогов', { numbering: { reference: 'bullets', level: 0 } }),
      p('Обратная связь — оценка качества ответа', { numbering: { reference: 'bullets', level: 0 } }),
      p('Источники ответа — ссылки на документы-источники', { numbering: { reference: 'bullets', level: 0 } }),
      p('Горячие клавиши — ускоренная работа с интерфейсом', { numbering: { reference: 'bullets', level: 0 } }),

      // 8
      p('8. Преимущества и недостатки', { heading: HeadingLevel.HEADING_1 }),
      p('8.1. Недостатки (подлежащие исправлению)', { heading: HeadingLevel.HEADING_2 }),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3000, 6026],
        rows: [
          tableRow([{ text: 'Недостаток', bold: true }, { text: 'Описание', bold: true }], true),
          tableRow(['Отсутствие кэширования', 'На один и тот же вопрос модель отвечает заново']),
          tableRow(['Риск некорректных ответов', 'Неверный ответ сохраняется и показывается пользователям']),
          tableRow(['Зависимость от RouterAI', 'Данные запросов уходят в облако — проблема конфиденциальности']),
          tableRow(['Нет автообновления базы', 'При обновлении нормативной базы документы обновляются вручную']),
          tableRow(['Обновление только через программиста', 'Нет интерфейса для самостоятельного обновления']),
        ]
      }),

      p('8.2. Преимущества', { heading: HeadingLevel.HEADING_2 }),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3000, 6026],
        rows: [
          tableRow([{ text: 'Преимущество', bold: true }, { text: 'Описание', bold: true }], true),
          tableRow(['Низкие требования к ресурсам', 'Не требуется GPU, система работает на CPU']),
          tableRow(['ИИ-агенты', 'Переформулирование запросов, разбиение сложных вопросов']),
          tableRow(['Гибридный поиск', '3 вектора + BM25 — высокая релевантность']),
          tableRow(['Быстрое время ответа', 'Диффузионная модель mercury-2']),
          tableRow(['Система аналитики', 'Запись всех чатов и пользователей']),
          tableRow(['Обратная связь', 'Возможность оценки качества ответов']),
        ]
      }),

      // 9
      p('9. Технические требования и инфраструктура', { heading: HeadingLevel.HEADING_1 }),
      p('9.1. Минимальные требования к серверу', { heading: HeadingLevel.HEADING_2 }),
      new Table({
        width: { size: 9026, type: WidthType.DXA },
        columnWidths: [3000, 6026],
        rows: [
          tableRow([{ text: 'Ресурс', bold: true }, { text: 'Требование', bold: true }], true),
          tableRow(['Процессор', '4 ядра']),
          tableRow(['Оперативная память', '4–8 ГБ']),
          tableRow(['Дисковое пространство', 'от 10 ГБ (зависит от объёма логов)']),
        ]
      }),

      p('9.2. Финансовые затраты', { heading: HeadingLevel.HEADING_2 }),
      p('Основные расходы — подписка на сервис RouterAI для доступа к языковым моделям.'),

      p('9.3. Контейнеризация', { heading: HeadingLevel.HEADING_2 }),
      p('Система развёрнута через Docker Compose:'),
      p('Backend: FastAPI + Uvicorn', { numbering: { reference: 'bullets', level: 0 } }),
      p('Frontend: Vue.js 3 + Nginx', { numbering: { reference: 'bullets', level: 0 } }),
      p('Qdrant: векторная база данных', { numbering: { reference: 'bullets', level: 0 } }),
      p('Supabase: PostgreSQL + Auth', { numbering: { reference: 'bullets', level: 0 } }),

      // 10
      p('10. Условия тиражирования', { heading: HeadingLevel.HEADING_1 }),
      p('Для развёртывания системы на внутреннем контуре заказчика:'),
      p('Предоставить сервер с указанными характеристиками', { numbering: { reference: 'bullets', level: 0 } }),
      p('Настроить Docker и Docker Compose', { numbering: { reference: 'bullets', level: 0 } }),
      p('Развернуть контейнеры из репозитория', { numbering: { reference: 'bullets', level: 0 } }),
      p('Настроить подключение к внутреннему Supabase (при необходимости)', { numbering: { reference: 'bullets', level: 0 } }),
      p('При желании — заменить RouterAI на локальную модель (требует GPU)', { numbering: { reference: 'bullets', level: 0 } }),

      // 11
      p('11. Заключение', { heading: HeadingLevel.HEADING_1 }),
      p('Разработанная система ИИ-ассистента демонстрирует работоспособность подхода Agentic RAG с гибридным поиском. Система готова к тестированию и внедрению, при этом существует ряд направлений для улучшения: кэширование запросов, автоматическое обновление базы знаний, локализация языковых моделей для повышения безопасности данных.'),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('d:\\ai_assistant\\practice\\report.docx', buffer);
  console.log('Done');
}).catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
