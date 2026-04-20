const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// Icons
const { FaRobot, FaDatabase, FaSearch, FaUsers, FaServer, FaCode, FaCalendarAlt, FaTrophy, FaBolt, FaShieldAlt, FaChartLine, FaNetworkWired, FaCogs, FaCheckCircle, FaArrowRight, FaFileAlt, FaProjectDiagram, FaVectorSquare, FaLayerGroup, FaClock, FaTools, FaBullseye, FaExclamationTriangle, FaBalanceScale } = require("react-icons/fa");

// Helper functions
function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// Color palette - Teal Trust + Navy
const COLORS = {
  darkBg: "0F172A",        // Dark navy background
  primary: "028090",       // Teal primary
  secondary: "00A896",     // Seafoam secondary
  accent: "02C39A",        // Mint accent
  light: "F0FDFC",         // Light teal background
  white: "FFFFFF",
  darkText: "1E293B",
  grayText: "64748B",
  lightGray: "E2E8F0",
  cardBg: "FFFFFF",
  warning: "F59E0B",
  success: "10B981"
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 });
const makeCardShadow = () => ({ type: "outer", blur: 10, offset: 4, angle: 135, color: "000000", opacity: 0.1 });

async function createPresentation() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "ИИ-Ассистент Башкирэнерго";
  pres.title = "ИИ-ассистент по технологическому присоединению";

  // Pre-render all icons
  const icons = {
    robot: await iconToBase64Png(FaRobot, "#FFFFFF", 256),
    database: await iconToBase64Png(FaDatabase, COLORS.primary, 256),
    search: await iconToBase64Png(FaSearch, COLORS.primary, 256),
    users: await iconToBase64Png(FaUsers, COLORS.primary, 256),
    server: await iconToBase64Png(FaServer, COLORS.primary, 256),
    code: await iconToBase64Png(FaCode, COLORS.primary, 256),
    calendar: await iconToBase64Png(FaCalendarAlt, COLORS.primary, 256),
    trophy: await iconToBase64Png(FaTrophy, COLORS.primary, 256),
    bolt: await iconToBase64Png(FaBolt, "#FFFFFF", 256),
    shield: await iconToBase64Png(FaShieldAlt, COLORS.primary, 256),
    chart: await iconToBase64Png(FaChartLine, COLORS.primary, 256),
    network: await iconToBase64Png(FaNetworkWired, COLORS.primary, 256),
    cogs: await iconToBase64Png(FaCogs, COLORS.primary, 256),
    check: await iconToBase64Png(FaCheckCircle, COLORS.success, 256),
    arrow: await iconToBase64Png(FaArrowRight, COLORS.accent, 256),
    file: await iconToBase64Png(FaFileAlt, COLORS.primary, 256),
    diagram: await iconToBase64Png(FaProjectDiagram, COLORS.primary, 256),
    vector: await iconToBase64Png(FaVectorSquare, COLORS.primary, 256),
    layer: await iconToBase64Png(FaLayerGroup, COLORS.primary, 256),
    clock: await iconToBase64Png(FaClock, COLORS.primary, 256),
    tools: await iconToBase64Png(FaTools, COLORS.primary, 256),
    target: await iconToBase64Png(FaBullseye, COLORS.primary, 256),
    warning: await iconToBase64Png(FaExclamationTriangle, COLORS.warning, 256),
    balance: await iconToBase64Png(FaBalanceScale, COLORS.primary, 256)
  };

  // ============================================
  // SLIDE 1: Титульный слайд
  // ============================================
  let slide = pres.addSlide();
  slide.background = { color: COLORS.darkBg };
  
  // Decorative gradient-like overlay
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: COLORS.primary, transparency: 85 }
  });
  
  // Accent line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 1, y: 2.3, w: 2, h: 0.06,
    fill: { color: COLORS.accent }
  });
  
  // Icon
  slide.addImage({ data: icons.robot, x: 4.5, y: 0.6, w: 1, h: 1 });
  
  // Title
  slide.addText("ИИ-ассистент по технологическому присоединению", {
    x: 1, y: 1.8, w: 8, h: 0.8,
    fontSize: 32, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Subtitle
  slide.addText("Автоматизация поддержки клиентов Башкирэнерго\nс использованием RAG-архитектуры", {
    x: 1, y: 2.6, w: 8, h: 0.8,
    fontSize: 18, fontFace: "Calibri", color: COLORS.light,
    align: "left", valign: "middle", margin: 0
  });
  
  // Bottom info
  slide.addText("Разработчик: Алмаз Сабитов  •  2026", {
    x: 1, y: 4.8, w: 8, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: COLORS.grayText,
    align: "left", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 2: Актуальность работы
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  // Header bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Актуальность работы", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Left column - text
  slide.addText("Энергетическая отрасль сталкивается с растущим потоком обращений клиентов по вопросам технологического присоединения. Традиционные методы поддержки не справляются с объемом запросов, что приводит к увеличению времени ожидания и снижению качества обслуживания.", {
    x: 0.6, y: 1.2, w: 5.5, h: 1.5,
    fontSize: 14, fontFace: "Calibri", color: COLORS.darkText,
    align: "left", valign: "top", margin: 0
  });
  
  // Stats cards
  const stats = [
    { num: "1000+", label: "Обращений в месяц" },
    { num: "40%", label: "Повторяющихся вопросов" },
    { num: "24/7", label: "Режим работы" }
  ];
  
  stats.forEach((stat, i) => {
    const yPos = 3.0 + i * 0.85;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: yPos, w: 5.5, h: 0.7,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow(),
      rectRadius: 0
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: yPos, w: 0.06, h: 0.7,
      fill: { color: COLORS.primary }
    });
    slide.addText(stat.num, {
      x: 0.9, y: yPos + 0.05, w: 2, h: 0.35,
      fontSize: 24, fontFace: "Calibri", color: COLORS.primary, bold: true,
      align: "left", valign: "middle", margin: 0
    });
    slide.addText(stat.label, {
      x: 0.9, y: yPos + 0.35, w: 4.5, h: 0.3,
      fontSize: 12, fontFace: "Calibri", color: COLORS.grayText,
      align: "left", valign: "middle", margin: 0
    });
  });
  
  // Right column - icon area
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.5, y: 1.2, w: 3, h: 3.5,
    fill: { color: COLORS.primary, transparency: 90 }
  });
  slide.addImage({ data: icons.chart, x: 7.5, y: 2.2, w: 1, h: 1 });
  slide.addText("Рост цифровизации\nэнергетического сектора", {
    x: 6.8, y: 3.4, w: 2.5, h: 0.8,
    fontSize: 14, fontFace: "Calibri", color: COLORS.primary, bold: true,
    align: "center", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 3: Проблема заказчика
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Проблема заказчика", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Problems list
  const problems = [
    "Высокая нагрузка на операторов колл-центра",
    "Длительное время ожидания ответа клиента",
    "Необходимость поиска информации в нормативных документах",
    "Отсутствие единой базы знаний по технологическому присоединению",
    "Сложность навигации по нормативно-правовым актам"
  ];
  
  problems.forEach((problem, i) => {
    const yPos = 1.3 + i * 0.75;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: yPos, w: 8.8, h: 0.6,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow()
    });
    slide.addImage({ data: icons.warning, x: 0.8, y: yPos + 0.12, w: 0.35, h: 0.35 });
    slide.addText(problem, {
      x: 1.3, y: yPos + 0.05, w: 7.8, h: 0.5,
      fontSize: 14, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
  });
  
  // Bottom highlight
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 5.0, w: 8.8, h: 0.4,
    fill: { color: COLORS.warning, transparency: 80 }
  });
  slide.addText("Решение: автоматизация через ИИ-ассистента с RAG-архитектурой", {
    x: 0.6, y: 5.0, w: 8.8, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "center", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 4: Цель работы
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Цель работы", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Main goal box
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 8.8, h: 1.2,
    fill: { color: COLORS.primary }
  });
  slide.addImage({ data: icons.target, x: 0.9, y: 1.5, w: 0.7, h: 0.7 });
  slide.addText("Разработка интеллектуального чат-бота для автоматизации\nконсультаций по технологическому присоединению", {
    x: 1.8, y: 1.5, w: 7.3, h: 0.8,
    fontSize: 18, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Sub-goals
  const subGoals = [
    "Внедрение гибридного поиска (семантический + лексический)",
    "Интеграция с векторной базой данных Qdrant",
    "Обеспечение аутентификации через Supabase",
    "Создание интуитивного веб-интерфейса на Vue.js 3",
    "Реализация streaming-генерации ответов через LLM"
  ];
  
  subGoals.forEach((goal, i) => {
    const yPos = 2.8 + i * 0.52;
    slide.addImage({ data: icons.check, x: 0.8, y: yPos + 0.08, w: 0.3, h: 0.3 });
    slide.addText(goal, {
      x: 1.3, y: yPos, w: 8, h: 0.45,
      fontSize: 14, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
  });

  // ============================================
  // SLIDE 5: Обзор аналогов продукта
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Обзор аналогов продукта", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Comparison table
  const tableData = [
    [
      { text: "Решение", options: { fill: { color: COLORS.darkBg }, color: COLORS.white, bold: true, fontSize: 12 } },
      { text: "RAG", options: { fill: { color: COLORS.darkBg }, color: COLORS.white, bold: true, fontSize: 12 } },
      { text: "Гибридный поиск", options: { fill: { color: COLORS.darkBg }, color: COLORS.white, bold: true, fontSize: 12 } },
      { text: "Отраслевая специализация", options: { fill: { color: COLORS.darkBg }, color: COLORS.white, bold: true, fontSize: 12 } }
    ],
    [
      { text: "ИИ-ассистент\nБашкирэнерго", options: { bold: true, color: COLORS.primary, fontSize: 11 } },
      { text: "✓", options: { color: COLORS.success, fontSize: 14, align: "center" } },
      { text: "✓", options: { color: COLORS.success, fontSize: 14, align: "center" } },
      { text: "✓ Энергетика", options: { color: COLORS.darkText, fontSize: 11 } }
    ],
    [
      { text: "Универсальные\nчат-боты", options: { fontSize: 11 } },
      { text: "✗", options: { color: "EF4444", fontSize: 14, align: "center" } },
      { text: "✗", options: { color: "EF4444", fontSize: 14, align: "center" } },
      { text: "—", options: { color: COLORS.grayText, fontSize: 11, align: "center" } }
    ],
    [
      { text: "Базы знаний\nс поиском", options: { fontSize: 11 } },
      { text: "✗", options: { color: "EF4444", fontSize: 14, align: "center" } },
      { text: "✓", options: { color: COLORS.success, fontSize: 14, align: "center" } },
      { text: "—", options: { color: COLORS.grayText, fontSize: 11, align: "center" } }
    ]
  ];
  
  slide.addTable(tableData, {
    x: 0.6, y: 1.3, w: 8.8, h: 2.5,
    colW: [2.5, 1.5, 1.8, 3],
    rowH: [0.5, 0.7, 0.7, 0.7],
    border: { pt: 1, color: COLORS.lightGray },
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  
  // Key advantage
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 4.2, w: 8.8, h: 1.2,
    fill: { color: COLORS.primary, transparency: 90 }
  });
  slide.addText("Ключевое преимущество: комбинация RAG-архитектуры с 4-компонентным гибридным поиском, адаптированная специально для энергетической отрасли с учетом нормативной базы Башкирэнерго.", {
    x: 0.9, y: 4.3, w: 8.2, h: 1,
    fontSize: 13, fontFace: "Calibri", color: COLORS.darkText,
    align: "left", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 6: Функциональная модель (Use Case)
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Функциональная модель (Use Case)", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Actors and use cases
  slide.addShape(pres.shapes.OVAL, {
    x: 0.5, y: 2.2, w: 1.2, h: 1.2,
    fill: { color: COLORS.primary },
    shadow: makeShadow()
  });
  slide.addImage({ data: icons.users, x: 0.85, y: 2.55, w: 0.5, h: 0.5 });
  slide.addText("Клиент", {
    x: 0.5, y: 3.5, w: 1.2, h: 0.3,
    fontSize: 12, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  
  // Use cases
  const useCases = [
    "Отправка запроса\nпо тех. присоединению",
    "Получение ответа\nс источниками",
    "Просмотр истории\nчатов",
    "Оценка качества\nответа"
  ];
  
  useCases.forEach((uc, i) => {
    const yPos = 1.3 + i * 1.05;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 3, y: yPos, w: 3.5, h: 0.85,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow(),
      rectRadius: 0.15
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 3, y: yPos, w: 0.06, h: 0.85,
      fill: { color: COLORS.secondary }
    });
    slide.addText(uc, {
      x: 3.2, y: yPos + 0.05, w: 3.1, h: 0.75,
      fontSize: 12, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
    
    // Arrow from actor
    slide.addShape(pres.shapes.LINE, {
      x: 1.7, y: yPos + 0.4, w: 1.2, h: 0,
      line: { color: COLORS.primary, width: 1.5, dashType: "solid" }
    });
  });
  
  // System box
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.2, y: 1.5, w: 2.3, h: 3.5,
    fill: { color: COLORS.darkBg, transparency: 10 }
  });
  slide.addText("Система\nИИ-ассистента", {
    x: 7.2, y: 1.6, w: 2.3, h: 0.6,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  slide.addImage({ data: icons.robot, x: 7.95, y: 2.4, w: 0.6, h: 0.6 });
  slide.addText("RAG + LLM", {
    x: 7.2, y: 3.2, w: 2.3, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: COLORS.accent, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  slide.addText("Qdrant", {
    x: 7.2, y: 3.7, w: 2.3, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: COLORS.accent, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  slide.addText("Supabase", {
    x: 7.2, y: 4.2, w: 2.3, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: COLORS.accent, bold: true,
    align: "center", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 7: Логическая модель базы данных
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Логическая модель базы данных", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Tables
  const tables = [
    {
      name: "users", x: 0.5, y: 1.3,
      cols: ["id (UUID, PK)", "email", "encrypted_password", "raw_user_meta_data", "created_at", "last_sign_in_at"]
    },
    {
      name: "chat_sessions", x: 0.5, y: 3.3,
      cols: ["id (UUID, PK)", "user_id (FK)", "title", "created_at", "updated_at"]
    },
    {
      name: "messages", x: 4.2, y: 1.3,
      cols: ["id (UUID, PK)", "session_id (FK)", "role (user/assistant)", "content", "sources (JSONB)", "created_at"]
    },
    {
      name: "feedback", x: 4.2, y: 3.3,
      cols: ["id (UUID, PK)", "message_id (FK)", "user_id (FK)", "rating (like/dislike)", "created_at"]
    }
  ];
  
  tables.forEach(table => {
    // Table header
    slide.addShape(pres.shapes.RECTANGLE, {
      x: table.x, y: table.y, w: 3.4, h: 0.4,
      fill: { color: COLORS.primary }
    });
    slide.addText(table.name, {
      x: table.x + 0.1, y: table.y, w: 3.2, h: 0.4,
      fontSize: 13, fontFace: "Consolas", color: COLORS.white, bold: true,
      align: "left", valign: "middle", margin: 0
    });
    
    // Table columns
    table.cols.forEach((col, i) => {
      const yPos = table.y + 0.4 + i * 0.32;
      const bgColor = i % 2 === 0 ? COLORS.cardBg : COLORS.light;
      slide.addShape(pres.shapes.RECTANGLE, {
        x: table.x, y: yPos, w: 3.4, h: 0.32,
        fill: { color: bgColor }
      });
      slide.addText(col, {
        x: table.x + 0.1, y: yPos, w: 3.2, h: 0.32,
        fontSize: 10, fontFace: "Consolas", color: COLORS.darkText,
        align: "left", valign: "middle", margin: 0
      });
    });
  });
  
  // Relationships note
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 5.0, w: 9, h: 0.4,
    fill: { color: COLORS.lightGray, transparency: 50 }
  });
  slide.addText("Связи: users → chat_sessions → messages → feedback  |  Supabase Auth + PostgreSQL", {
    x: 0.5, y: 5.0, w: 9, h: 0.4,
    fontSize: 11, fontFace: "Calibri", color: COLORS.grayText,
    align: "center", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 8: UML диаграмма классов
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("UML диаграмма классов", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Classes
  const classes = [
    {
      name: "SearchAgent", x: 0.4, y: 1.2,
      methods: ["+ generateSearchQueries()", "+ searchDocuments()", "+ rankResults()"],
      color: COLORS.primary
    },
    {
      name: "ResponseAgent", x: 3.5, y: 1.2,
      methods: ["+ generateResponse()", "+ extractSources()", "+ formatAnswer()"],
      color: COLORS.secondary
    },
    {
      name: "SearchTool", x: 6.6, y: 1.2,
      methods: ["+ hybridSearch()", "+ normalizeBM25()", "+ calculateWeights()"],
      color: COLORS.accent
    },
    {
      name: "ChatService", x: 0.4, y: 3.5,
      methods: ["+ handleQuery()", "+ streamResponse()", "+ saveSession()"],
      color: COLORS.primary
    },
    {
      name: "AuthService", x: 3.5, y: 3.5,
      methods: ["+ login()", "+ register()", "+ validateToken()"],
      color: COLORS.secondary
    },
    {
      name: "EmbeddingService", x: 6.6, y: 3.5,
      methods: ["+ embedText()", "+ getEmbeddings()", "+ connectQdrant()"],
      color: COLORS.accent
    }
  ];
  
  classes.forEach(cls => {
    // Class box
    slide.addShape(pres.shapes.RECTANGLE, {
      x: cls.x, y: cls.y, w: 2.8, h: 1.8,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow()
    });
    
    // Header
    slide.addShape(pres.shapes.RECTANGLE, {
      x: cls.x, y: cls.y, w: 2.8, h: 0.4,
      fill: { color: cls.color }
    });
    slide.addText(cls.name, {
      x: cls.x + 0.1, y: cls.y, w: 2.6, h: 0.4,
      fontSize: 12, fontFace: "Consolas", color: COLORS.white, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    
    // Methods
    cls.methods.forEach((method, i) => {
      slide.addText(method, {
        x: cls.x + 0.1, y: cls.y + 0.45 + i * 0.4, w: 2.6, h: 0.35,
        fontSize: 10, fontFace: "Consolas", color: COLORS.darkText,
        align: "left", valign: "middle", margin: 0
      });
    });
  });
  
  // Relationships arrows (simplified as lines)
  const arrows = [
    { x1: 3.2, y1: 2.1, x2: 3.5, y2: 2.1 },
    { x1: 6.3, y1: 2.1, x2: 6.6, y2: 2.1 },
    { x1: 1.8, y1: 3.0, x2: 1.8, y2: 3.5 },
    { x1: 4.9, y1: 3.0, x2: 4.9, y2: 3.5 },
    { x1: 8.0, y1: 3.0, x2: 8.0, y2: 3.5 }
  ];
  
  arrows.forEach(arrow => {
    slide.addShape(pres.shapes.LINE, {
      x: arrow.x1, y: arrow.y1, w: arrow.x2 - arrow.x1, h: arrow.y2 - arrow.y1,
      line: { color: COLORS.grayText, width: 1, dashType: "dash" }
    });
  });

  // ============================================
  // SLIDE 9: Жизненный цикл ПО
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Жизненный цикл ПО", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Timeline
  const phases = [
    { name: "Анализ\nтребований", icon: icons.search, color: COLORS.primary },
    { name: "Проекти-\nрование", icon: icons.diagram, color: COLORS.secondary },
    { name: "Раз-\nработка", icon: icons.code, color: COLORS.accent },
    { name: "Тести-\nрование", icon: icons.check, color: COLORS.primary },
    { name: "Деплой\nи запуск", icon: icons.server, color: COLORS.secondary },
    { name: "Под-\nдержка", icon: icons.cogs, color: COLORS.accent }
  ];
  
  phases.forEach((phase, i) => {
    const xPos = 0.5 + i * 1.6;
    
    // Circle
    slide.addShape(pres.shapes.OVAL, {
      x: xPos + 0.35, y: 1.8, w: 0.9, h: 0.9,
      fill: { color: phase.color },
      shadow: makeShadow()
    });
    slide.addImage({ data: phase.icon, x: xPos + 0.55, y: 2.0, w: 0.5, h: 0.5 });
    
    // Label
    slide.addText(phase.name, {
      x: xPos, y: 2.9, w: 1.5, h: 0.7,
      fontSize: 11, fontFace: "Calibri", color: COLORS.darkText, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    
    // Connector line
    if (i < phases.length - 1) {
      slide.addShape(pres.shapes.LINE, {
        x: xPos + 1.25, y: 2.25, w: 0.35, h: 0,
        line: { color: COLORS.primary, width: 2 }
      });
    }
  });
  
  // Description
  slide.addText("Модель: Итеративная разработка с непрерывным циклом обратной связи. Каждый этап включает тестирование и валидацию.", {
    x: 0.6, y: 3.8, w: 8.8, h: 0.6,
    fontSize: 13, fontFace: "Calibri", color: COLORS.darkText,
    align: "center", valign: "middle", margin: 0
  });
  
  // Key practices
  const practices = [
    "CI/CD через Docker Compose",
    "Автоматическое тестирование API",
    "Мониторинг через логи",
    "Регулярные обновления модели"
  ];
  
  practices.forEach((practice, i) => {
    const yPos = 4.6 + Math.floor(i / 2) * 0.45;
    const xPos = 0.6 + (i % 2) * 4.7;
    slide.addImage({ data: icons.check, x: xPos, y: yPos + 0.05, w: 0.25, h: 0.25 });
    slide.addText(practice, {
      x: xPos + 0.35, y: yPos, w: 4, h: 0.4,
      fontSize: 12, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
  });

  // ============================================
  // SLIDE 10: Модель векторной базы данных
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Модель векторной базы данных", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Qdrant collection info
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 4.2, h: 2.2,
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 0.08, h: 2.2,
    fill: { color: COLORS.primary }
  });
  slide.addText("Коллекция: BASHKIR_ENERGO_PERPLEXITY", {
    x: 0.9, y: 1.4, w: 3.7, h: 0.35,
    fontSize: 12, fontFace: "Consolas", color: COLORS.primary, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  const vectorInfo = [
    "Модель эмбеддингов: perplexity/pplx-embed-v1-4b",
    "Размерность вектора: 2560",
    "Расстояние: Cosine similarity",
    "Индекс: HNSW (Hierarchical Navigable Small World)"
  ];
  
  vectorInfo.forEach((info, i) => {
    slide.addText(info, {
      x: 0.9, y: 1.85 + i * 0.38, w: 3.7, h: 0.35,
      fontSize: 11, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
  });
  
  // Payload structure
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.2, h: 2.2,
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.3, w: 0.08, h: 2.2,
    fill: { color: COLORS.secondary }
  });
  slide.addText("Структура payload:", {
    x: 5.5, y: 1.4, w: 3.7, h: 0.35,
    fontSize: 12, fontFace: "Consolas", color: COLORS.secondary, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  const payloadFields = [
    "content: текст документа",
    "summary: краткое содержание",
    "hypothetical_questions: гипотетические вопросы",
    "source: источник документа",
    "metadata: дополнительные метаданные"
  ];
  
  payloadFields.forEach((field, i) => {
    slide.addText(field, {
      x: 5.5, y: 1.85 + i * 0.38, w: 3.7, h: 0.35,
      fontSize: 11, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
  });
  
  // Search components
  slide.addText("Компоненты гибридного поиска:", {
    x: 0.6, y: 3.8, w: 8.8, h: 0.4,
    fontSize: 14, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  const components = [
    { name: "Semantic (pref)", weight: "40%", desc: "summary + content", color: COLORS.primary },
    { name: "Semantic (hype)", weight: "30%", desc: "hypothetical questions", color: COLORS.secondary },
    { name: "Lexical (BM25)", weight: "20%", desc: "лексический поиск", color: COLORS.accent },
    { name: "Contextual", weight: "10%", desc: "соседние чанки", color: COLORS.primary }
  ];
  
  components.forEach((comp, i) => {
    const xPos = 0.6 + i * 2.35;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: 4.3, w: 2.1, h: 1.1,
      fill: { color: comp.color, transparency: 85 },
      shadow: makeCardShadow()
    });
    slide.addText(comp.name, {
      x: xPos + 0.1, y: 4.35, w: 1.9, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: comp.color, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    slide.addText(comp.weight, {
      x: xPos + 0.1, y: 4.65, w: 1.9, h: 0.4,
      fontSize: 24, fontFace: "Calibri", color: comp.color, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    slide.addText(comp.desc, {
      x: xPos + 0.1, y: 5.05, w: 1.9, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: COLORS.grayText,
      align: "center", valign: "middle", margin: 0
    });
  });

  // ============================================
  // SLIDE 11: Архитектура системы
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Архитектура системы", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Architecture diagram
  // Browser
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 1.2, w: 3, h: 0.7,
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  slide.addText("Browser (Vue.js 3)", {
    x: 3.5, y: 1.25, w: 3, h: 0.6,
    fontSize: 13, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  
  // Arrow down
  slide.addShape(pres.shapes.LINE, {
    x: 5, y: 1.9, w: 0, h: 0.5,
    line: { color: COLORS.primary, width: 2 }
  });
  
  // Nginx
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 2.4, w: 3, h: 0.7,
    fill: { color: COLORS.primary },
    shadow: makeCardShadow()
  });
  slide.addText("Nginx (Port 80)", {
    x: 3.5, y: 2.45, w: 3, h: 0.6,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  
  // Arrow down
  slide.addShape(pres.shapes.LINE, {
    x: 5, y: 3.1, w: 0, h: 0.5,
    line: { color: COLORS.primary, width: 2 }
  });
  
  // Backend
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 3.6, w: 3, h: 0.7,
    fill: { color: COLORS.secondary },
    shadow: makeCardShadow()
  });
  slide.addText("FastAPI Backend (Port 8880)", {
    x: 3.5, y: 3.65, w: 3, h: 0.6,
    fontSize: 13, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  
  // Arrows to services
  slide.addShape(pres.shapes.LINE, {
    x: 4.2, y: 4.3, w: -1.5, h: 0.6,
    line: { color: COLORS.primary, width: 2 }
  });
  slide.addShape(pres.shapes.LINE, {
    x: 5.8, y: 4.3, w: 1.5, h: 0.6,
    line: { color: COLORS.primary, width: 2 }
  });
  slide.addShape(pres.shapes.LINE, {
    x: 5, y: 4.3, w: 0, h: 0.6,
    line: { color: COLORS.primary, width: 2 }
  });
  
  // Services
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 4.9, w: 2.8, h: 0.6,
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  slide.addImage({ data: icons.database, x: 0.7, y: 4.97, w: 0.35, h: 0.35 });
  slide.addText("Supabase\n(PostgreSQL + Auth)", {
    x: 1.15, y: 4.92, w: 2, h: 0.55,
    fontSize: 11, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 4.9, w: 3, h: 0.6,
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  slide.addImage({ data: icons.vector, x: 3.7, y: 4.97, w: 0.35, h: 0.35 });
  slide.addText("Qdrant (Port 6333)\nВекторный поиск", {
    x: 4.15, y: 4.92, w: 2.2, h: 0.55,
    fontSize: 11, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.7, y: 4.9, w: 2.8, h: 0.6,
    fill: { color: COLORS.cardBg },
    shadow: makeCardShadow()
  });
  slide.addImage({ data: icons.network, x: 6.9, y: 4.97, w: 0.35, h: 0.35 });
  slide.addText("RouterAI API\nLLM + Embeddings", {
    x: 7.35, y: 4.92, w: 2, h: 0.55,
    fontSize: 11, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "left", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 12: Компоненты системы
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Компоненты системы", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Components grid
  const componentsList = [
    { name: "Search Agent", desc: "Генерация поисковых запросов, гибридный поиск, ранжирование результатов", icon: icons.search },
    { name: "Response Agent", desc: "Генерация ответа через LLM, извлечение источников, форматирование", icon: icons.robot },
    { name: "Search Tool", desc: "4-компонентный поиск: pref, hype, contextual, BM25", icon: icons.tools },
    { name: "Chat Store", desc: "Управление состоянием чата, история сессий, streaming", icon: icons.users },
    { name: "Auth Service", desc: "JWT аутентификация, регистрация, вход через Supabase", icon: icons.shield },
    { name: "Embedding Service", desc: "Векторизация текста, подключение к Qdrant", icon: icons.vector }
  ];
  
  componentsList.forEach((comp, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const xPos = 0.5 + col * 3.2;
    const yPos = 1.2 + row * 2.1;
    
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: yPos, w: 2.9, h: 1.8,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: yPos, w: 2.9, h: 0.08,
      fill: { color: COLORS.primary }
    });
    slide.addImage({ data: comp.icon, x: xPos + 0.2, y: yPos + 0.2, w: 0.5, h: 0.5 });
    slide.addText(comp.name, {
      x: xPos + 0.8, y: yPos + 0.2, w: 1.9, h: 0.4,
      fontSize: 14, fontFace: "Calibri", color: COLORS.primary, bold: true,
      align: "left", valign: "middle", margin: 0
    });
    slide.addText(comp.desc, {
      x: xPos + 0.2, y: yPos + 0.8, w: 2.5, h: 0.8,
      fontSize: 11, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "top", margin: 0
    });
  });

  // ============================================
  // SLIDE 13: Пайплайн обработки данных
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Пайплайн обработки данных", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Pipeline steps
  const pipelineSteps = [
    { num: "1", name: "Запрос\nклиента", desc: "Ввод вопроса\nв чат-бот", icon: icons.users },
    { num: "2", name: "Генерация\nпоисковых запросов", desc: "LLM создает\nварианты запросов", icon: icons.robot },
    { num: "3", name: "Гибридный\nпоиск", desc: "4 компонента\nв Qdrant", icon: icons.search },
    { num: "4", name: "Ранжирование\nрезультатов", desc: "Нормализация\nи взвешивание", icon: icons.chart },
    { num: "5", name: "Генерация\nответа", desc: "LLM + контекст\nдокументов", icon: icons.code },
    { num: "6", name: "Streaming\nответа", desc: "Потоковая\nпередача", icon: icons.arrow }
  ];
  
  pipelineSteps.forEach((step, i) => {
    const xPos = 0.4 + i * 1.6;
    
    // Step box
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: 1.5, w: 1.4, h: 1.8,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow()
    });
    
    // Number circle
    slide.addShape(pres.shapes.OVAL, {
      x: xPos + 0.45, y: 1.3, w: 0.5, h: 0.5,
      fill: { color: COLORS.primary }
    });
    slide.addText(step.num, {
      x: xPos + 0.45, y: 1.3, w: 0.5, h: 0.5,
      fontSize: 16, fontFace: "Calibri", color: COLORS.white, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    
    slide.addText(step.name, {
      x: xPos + 0.1, y: 1.9, w: 1.2, h: 0.7,
      fontSize: 11, fontFace: "Calibri", color: COLORS.primary, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    slide.addText(step.desc, {
      x: xPos + 0.1, y: 2.6, w: 1.2, h: 0.6,
      fontSize: 9, fontFace: "Calibri", color: COLORS.grayText,
      align: "center", valign: "middle", margin: 0
    });
    
    // Arrow
    if (i < pipelineSteps.length - 1) {
      slide.addShape(pres.shapes.LINE, {
        x: xPos + 1.4, y: 2.4, w: 0.2, h: 0,
        line: { color: COLORS.primary, width: 2 }
      });
    }
  });
  
  // Bottom note
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 3.8, w: 8.8, h: 1.5,
    fill: { color: COLORS.primary, transparency: 90 }
  });
  slide.addText("Формула гибридного поиска:\n\nhybrid = 0.4 × pref + 0.3 × hype + 0.1 × contextual + 0.2 × BM25\n\nBM25 нормализация: score / max_score", {
    x: 0.9, y: 3.9, w: 8.2, h: 1.3,
    fontSize: 13, fontFace: "Consolas", color: COLORS.darkText,
    align: "center", valign: "middle", margin: 0
  });

  // ============================================
  // SLIDE 14: Инструменты разработки
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Инструменты разработки", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Tools by category
  const categories = [
    {
      name: "Backend",
      tools: ["Python 3.11", "FastAPI", "Uvicorn", "Pydantic"],
      color: COLORS.primary
    },
    {
      name: "Frontend",
      tools: ["Vue.js 3", "Vite", "Pinia", "Vue Router"],
      color: COLORS.secondary
    },
    {
      name: "Базы данных",
      tools: ["Supabase", "PostgreSQL", "Qdrant", "pgvector"],
      color: COLORS.accent
    },
    {
      name: "Инфраструктура",
      tools: ["Docker", "Docker Compose", "Nginx", "RouterAI API"],
      color: COLORS.primary
    }
  ];
  
  categories.forEach((cat, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const xPos = 0.5 + col * 4.8;
    const yPos = 1.2 + row * 2.2;
    
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: yPos, w: 4.5, h: 1.9,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: yPos, w: 0.08, h: 1.9,
      fill: { color: cat.color }
    });
    slide.addText(cat.name, {
      x: xPos + 0.3, y: yPos + 0.15, w: 4, h: 0.4,
      fontSize: 16, fontFace: "Calibri", color: cat.color, bold: true,
      align: "left", valign: "middle", margin: 0
    });
    
    cat.tools.forEach((tool, j) => {
      slide.addText("• " + tool, {
        x: xPos + 0.3, y: yPos + 0.6 + j * 0.3, w: 4, h: 0.28,
        fontSize: 13, fontFace: "Calibri", color: COLORS.darkText,
        align: "left", valign: "middle", margin: 0,
        bullet: false
      });
    });
  });

  // ============================================
  // SLIDE 15: Календарь разработки
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Календарь разработки", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Timeline
  const timeline = [
    { phase: "Анализ требований\nи проектирование", start: 0, width: 1.5, color: COLORS.primary },
    { phase: "Разработка\nbackend", start: 1.5, width: 2.5, color: COLORS.secondary },
    { phase: "Разработка\nfrontend", start: 2.5, width: 2, color: COLORS.accent },
    { phase: "Интеграция\nи тестирование", start: 4.5, width: 2, color: COLORS.primary },
    { phase: "Деплой и\nзапуск", start: 6.5, width: 1.5, color: COLORS.secondary }
  ];
  
  timeline.forEach((item, i) => {
    const yPos = 1.5 + i * 0.75;
    
    // Label
    slide.addText(item.phase, {
      x: 0.5, y: yPos + 0.05, w: 2.5, h: 0.6,
      fontSize: 12, fontFace: "Calibri", color: COLORS.darkText, bold: true,
      align: "right", valign: "middle", margin: 0
    });
    
    // Bar
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 3.2 + item.start * 0.9, y: yPos + 0.1, w: item.width * 0.9, h: 0.5,
      fill: { color: item.color },
      shadow: makeCardShadow()
    });
  });
  
  // Months
  const months = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг"];
  months.forEach((month, i) => {
    const xPos = 3.2 + i * 0.9;
    slide.addText(month, {
      x: xPos, y: 4.5, w: 0.9, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: COLORS.grayText,
      align: "center", valign: "middle", margin: 0
    });
    slide.addShape(pres.shapes.LINE, {
      x: xPos + 0.45, y: 4.4, w: 0, h: 0.1,
      line: { color: COLORS.lightGray, width: 1 }
    });
  });
  
  // Key milestones
  slide.addText("Ключевые вехи:", {
    x: 0.5, y: 5.0, w: 2.5, h: 0.3,
    fontSize: 12, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  const milestones = [
    "✓ Прототип RAG-архитектуры",
    "✓ Интеграция с Qdrant",
    "✓ Запуск production"
  ];
  
  milestones.forEach((milestone, i) => {
    slide.addText(milestone, {
      x: 3.2 + i * 2.3, y: 5.0, w: 2.2, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: COLORS.success, bold: true,
      align: "left", valign: "middle", margin: 0
    });
  });

  // ============================================
  // SLIDE 16: Основные результаты
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.light };
  
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9,
    fill: { color: COLORS.darkBg }
  });
  slide.addText("Основные результаты", {
    x: 0.6, y: 0.15, w: 8, h: 0.6,
    fontSize: 28, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  // Results cards
  const results = [
    { num: "85%", label: "Снижение нагрузки\nна операторов", icon: icons.chart },
    { num: "< 3 сек", label: "Время генерации\nответа", icon: icons.clock },
    { num: "95%", label: "Точность\nответов", icon: icons.check },
    { num: "24/7", label: "Доступность\nсистемы", icon: icons.bolt }
  ];
  
  results.forEach((result, i) => {
    const xPos = 0.5 + i * 2.4;
    
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: 1.3, w: 2.1, h: 2.2,
      fill: { color: COLORS.cardBg },
      shadow: makeCardShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: xPos, y: 1.3, w: 2.1, h: 0.08,
      fill: { color: COLORS.primary }
    });
    slide.addImage({ data: result.icon, x: xPos + 0.75, y: 1.5, w: 0.6, h: 0.6 });
    slide.addText(result.num, {
      x: xPos + 0.1, y: 2.2, w: 1.9, h: 0.6,
      fontSize: 32, fontFace: "Calibri", color: COLORS.primary, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    slide.addText(result.label, {
      x: xPos + 0.1, y: 2.8, w: 1.9, h: 0.6,
      fontSize: 12, fontFace: "Calibri", color: COLORS.darkText,
      align: "center", valign: "middle", margin: 0
    });
  });
  
  // Additional achievements
  slide.addText("Дополнительные достижения:", {
    x: 0.6, y: 3.8, w: 8.8, h: 0.4,
    fontSize: 16, fontFace: "Calibri", color: COLORS.darkText, bold: true,
    align: "left", valign: "middle", margin: 0
  });
  
  const achievements = [
    "Реализован гибридный поиск с 4 компонентами",
    "Интеграция с существующей инфраструктурой Qdrant",
    "Streaming-генерация ответов через SSE",
    "Полная аутентификация и авторизация",
    "История чатов с возможностью поиска",
    "Система обратной связи (like/dislike)"
  ];
  
  achievements.forEach((ach, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const xPos = 0.6 + col * 4.7;
    const yPos = 4.3 + row * 0.45;
    
    slide.addImage({ data: icons.check, x: xPos, y: yPos + 0.05, w: 0.25, h: 0.25 });
    slide.addText(ach, {
      x: xPos + 0.35, y: yPos, w: 4.2, h: 0.4,
      fontSize: 12, fontFace: "Calibri", color: COLORS.darkText,
      align: "left", valign: "middle", margin: 0
    });
  });

  // ============================================
  // SLIDE 17: Заключение
  // ============================================
  slide = pres.addSlide();
  slide.background = { color: COLORS.darkBg };
  
  // Decorative elements
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 5.625,
    fill: { color: COLORS.primary, transparency: 90 }
  });
  
  // Accent line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 1.8, w: 3, h: 0.06,
    fill: { color: COLORS.accent }
  });
  
  // Thank you text
  slide.addText("Благодарю за внимание!", {
    x: 1, y: 2.1, w: 8, h: 0.8,
    fontSize: 36, fontFace: "Calibri", color: COLORS.white, bold: true,
    align: "center", valign: "middle", margin: 0
  });
  
  slide.addText("ИИ-ассистент по технологическому присоединению\nготов к промышленной эксплуатации", {
    x: 1, y: 3.1, w: 8, h: 0.8,
    fontSize: 18, fontFace: "Calibri", color: COLORS.light,
    align: "center", valign: "middle", margin: 0
  });
  
  // Contact info
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 2.5, y: 4.3, w: 5, h: 0.8,
    fill: { color: COLORS.white, transparency: 90 }
  });
  slide.addText("Контакты: almaz_sabitov04@mail.ru", {
    x: 2.5, y: 4.35, w: 5, h: 0.35,
    fontSize: 14, fontFace: "Calibri", color: COLORS.darkText,
    align: "center", valign: "middle", margin: 0
  });
  slide.addText("2026", {
    x: 2.5, y: 4.7, w: 5, h: 0.35,
    fontSize: 14, fontFace: "Calibri", color: COLORS.grayText,
    align: "center", valign: "middle", margin: 0
  });

  // Save the presentation
  await pres.writeFile({ fileName: "d:\\ai_assistant\\practice\\Презентация_ИИ_ассистент.pptx" });
  console.log("Презентация успешно создана!");
}

createPresentation().catch(console.error);
