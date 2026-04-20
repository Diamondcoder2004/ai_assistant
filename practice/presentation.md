---
marp: true
theme: default
paginate: true
backgroundColor: #F0FDFC
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  
  :root {
    --primary: #028090;
    --secondary: #00A896;
    --accent: #02C39A;
    --dark: #0F172A;
    --light: #F0FDFC;
    --gray: #64748B;
    --white: #FFFFFF;
  }
  
  section {
    font-family: 'Inter', sans-serif;
    padding: 40px 60px;
    background: linear-gradient(135deg, #F0FDFC 0%, #E0F2FE 100%);
    color: #1E293B;
  }
  
  section h1 {
    color: var(--dark);
    font-size: 2.5em;
    font-weight: 800;
    margin-bottom: 0.3em;
    border-bottom: 4px solid var(--primary);
    padding-bottom: 0.3em;
  }
  
  section h2 {
    color: var(--primary);
    font-size: 1.8em;
    font-weight: 700;
    margin-bottom: 0.5em;
  }
  
  section p, section li {
    font-size: 1.05em;
    line-height: 1.6;
  }
  
  section strong {
    color: var(--primary);
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin: 25px 0;
  }
  
  .stat-card {
    background: rgba(255, 255, 255, 0.1);
    border-left: 4px solid var(--accent);
    padding: 20px;
    border-radius: 8px;
    text-align: center;
  }
  
  .light-bg .stat-card {
    background: var(--white);
    border-left-color: var(--primary);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  .stat-number {
    font-size: 2.5em;
    font-weight: 800;
    color: var(--accent);
    display: block;
  }
  
  .light-bg .stat-number {
    color: var(--primary);
  }
  
  .stat-label {
    font-size: 0.85em;
    color: var(--gray);
    margin-top: 5px;
  }
  
  .two-column {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin: 20px 0;
  }
  
  .card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 18px;
  }
  
  .light-bg .card {
    background: var(--white);
    border-color: #E2E8F0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
  
  .icon-text {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0;
    font-size: 0.95em;
  }
  
  .icon-circle {
    width: 45px;
    height: 45px;
    border-radius: 50%;
    background: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3em;
    flex-shrink: 0;
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 0.9em;
  }
  
  table th {
    background: var(--primary);
    color: var(--white);
    padding: 10px;
    text-align: left;
  }
  
  table td {
    padding: 8px 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .light-bg table td {
    border-bottom-color: #E2E8F0;
  }
  
  table tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .light-bg table tr:nth-child(even) {
    background: #F8FAFC;
  }
  
  .highlight-box {
    background: rgba(2, 195, 154, 0.1);
    border-left: 4px solid var(--accent);
    padding: 15px;
    margin: 15px 0;
    border-radius: 0 8px 8px 0;
  }
  
  .light-bg .highlight-box {
    background: rgba(2, 128, 144, 0.1);
    border-left-color: var(--primary);
  }
  
  /* Use Case Diagram */
  .usecase-container {
    display: flex;
    gap: 30px;
    margin: 20px 0;
    align-items: flex-start;
  }
  
  .usecase-actor {
    text-align: center;
    flex: 0 0 120px;
  }
  
  .actor-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--primary);
    margin: 0 auto 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8em;
  }
  
  .usecase-system {
    flex: 1;
    border: 2px solid var(--primary);
    border-radius: 8px;
    padding: 20px;
    background: rgba(2, 128, 144, 0.05);
  }
  
  .light-bg .usecase-system {
    background: rgba(2, 128, 144, 0.03);
  }
  
  .usecase-item {
    background: var(--white);
    border: 2px solid var(--secondary);
    border-radius: 20px;
    padding: 10px 15px;
    margin: 10px 0;
    text-align: center;
    font-size: 0.9em;
    color: var(--dark);
  }
  
  /* Architecture Diagram */
  .arch-diagram {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    margin: 20px 0;
  }
  
  .arch-node {
    background: var(--white);
    border: 2px solid var(--primary);
    border-radius: 6px;
    padding: 10px 20px;
    text-align: center;
    font-weight: 600;
    font-size: 0.9em;
    color: var(--dark);
    min-width: 200px;
  }
  
  .arch-node.primary {
    background: var(--primary);
    color: var(--white);
    border-color: var(--dark);
  }
  
  .arch-node.secondary {
    background: var(--secondary);
    color: var(--white);
    border-color: var(--dark);
  }
  
  .arch-services {
    display: flex;
    gap: 20px;
    margin-top: 10px;
  }
  
  .arch-arrow {
    color: var(--primary);
    font-size: 1.5em;
    line-height: 1;
  }
  
  /* Timeline */
  .timeline {
    display: flex;
    justify-content: space-between;
    margin: 25px 0;
    position: relative;
  }
  
  .timeline::before {
    content: '';
    position: absolute;
    top: 25px;
    left: 5%;
    right: 5%;
    height: 4px;
    background: var(--primary);
  }
  
  .timeline-item {
    text-align: center;
    flex: 1;
    position: relative;
  }
  
  .timeline-dot {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: var(--accent);
    margin: 0 auto 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1.2em;
    color: var(--white);
    position: relative;
    z-index: 1;
  }
  
  .timeline-label {
    font-size: 0.8em;
    font-weight: 600;
  }
  
  /* Pipeline */
  .pipeline {
    display: flex;
    gap: 8px;
    margin: 20px 0;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .pipeline-step {
    background: var(--primary);
    color: var(--white);
    border-radius: 6px;
    padding: 12px 15px;
    text-align: center;
    font-size: 0.85em;
    font-weight: 600;
    min-width: 110px;
  }
  
  .pipeline-step:nth-child(odd) {
    background: var(--secondary);
  }
  
  .pipeline-arrow {
    color: var(--accent);
    font-size: 1.5em;
  }
  
  /* Gantt-like chart */
  .gantt-chart {
    margin: 20px 0;
  }
  
  .gantt-row {
    display: flex;
    align-items: center;
    margin: 8px 0;
    gap: 10px;
  }
  
  .gantt-label {
    flex: 0 0 180px;
    font-size: 0.85em;
    font-weight: 600;
    text-align: right;
  }
  
  .gantt-bar-container {
    flex: 1;
    display: flex;
    gap: 2px;
  }
  
  .gantt-month {
    flex: 1;
    text-align: center;
    font-size: 0.7em;
    color: var(--gray);
  }
  
  .gantt-bar {
    height: 25px;
    border-radius: 4px;
    background: var(--primary);
  }
  
  .gantt-bar.phase1 { background: var(--primary); }
  .gantt-bar.phase2 { background: var(--secondary); }
  .gantt-bar.phase3 { background: var(--accent); }
  
  /* Class diagram */
  .class-diagram {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin: 20px 0;
  }
  
  .class-box {
    background: var(--white);
    border: 2px solid var(--primary);
    border-radius: 6px;
    overflow: hidden;
  }
  
  .class-header {
    background: var(--primary);
    color: var(--white);
    padding: 8px;
    text-align: center;
    font-weight: 700;
    font-size: 0.9em;
  }
  
  .class-methods {
    padding: 8px;
    font-size: 0.75em;
    font-family: monospace;
  }
  
  .class-methods div {
    margin: 3px 0;
    color: var(--dark);
  }
  
  /* ER diagram */
  .er-diagram {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
    margin: 15px 0;
  }
  
  .er-table {
    background: var(--white);
    border: 2px solid var(--primary);
    border-radius: 6px;
    overflow: hidden;
  }
  
  .er-header {
    background: var(--primary);
    color: var(--white);
    padding: 8px 12px;
    font-weight: 700;
    font-size: 0.9em;
  }
  
  .er-fields {
    padding: 8px 12px;
    font-size: 0.75em;
    font-family: monospace;
  }
  
  .er-fields div {
    margin: 3px 0;
    color: var(--dark);
  }
  
  .er-relationships {
    margin-top: 15px;
    padding: 12px;
    background: rgba(2, 128, 144, 0.1);
    border-radius: 6px;
    font-size: 0.85em;
    text-align: center;
  }
  
  .light-bg .er-relationships {
    background: rgba(2, 128, 144, 0.05);
  }
  
  ul {
    margin: 10px 0;
    padding-left: 25px;
  }
  
  li {
    margin: 6px 0;
  }
  
  code {
    background: rgba(2, 128, 144, 0.1);
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9em;
  }
  
  .light-bg code {
    background: rgba(2, 128, 144, 0.15);
  }
---

<!-- Титульный слайд -->
# 🤖 ИИ-ассистент по технологическому присоединению

### Автоматизация поддержки клиентов Башкирэнерго с использованием RAG-архитектуры

---

---

# 📊 Актуальность работы

Энергетическая отрасль сталкивается с растущим потоком обращений клиентов по вопросам технологического присоединения. Традиционные методы поддержки не справляются с объемом запросов.

<div class="stats-grid">
  <div class="stat-card">
    <span class="stat-number">1000+</span>
    <span class="stat-label">Обращений в месяц</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">40%</span>
    <span class="stat-label">Повторяющихся вопросов</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">24/7</span>
    <span class="stat-label">Режим работы</span>
  </div>
</div>

<div class="highlight-box">
<strong>Цифровизация энергетического сектора</strong> требует внедрения автоматизированных систем поддержки
---

# ⚠️ Проблема заказчика

<div class="two-column">
  <div>
    <div class="icon-text">
      <div class="icon-circle">📞</div>
      <div>Высокая нагрузка на операторов колл-центра</div>
    </div>
    <div class="icon-text">
      <div class="icon-circle">⏱️</div>
      <div>Длительное время ожидания ответа клиента</div>
    </div>
    <div class="icon-text">
      <div class="icon-circle">📚</div>
      <div>Необходимость поиска в нормативных документах</div>
    </div>
  </div>
  <div>
    <div class="icon-text">
      <div class="icon-circle">🗄️</div>
      <div>Отсутствие единой базы знаний по тех. присоединению</div>
    </div>
    <div class="icon-text">
      <div class="icon-circle">🔍</div>
      <div>Сложность навигации по нормативно-правовым актам</div>
    </div>
  </div>
</div>

<div class="highlight-box">
<strong>Решение:</strong> автоматизация через ИИ-ассистента с RAG-архитектурой
---

# 🎯 Цель работы

<div class="card" style="background: var(--primary); color: white; padding: 20px; margin: 15px 0; border-radius: 8px;">
<h3 style="color: white; margin: 0 0 10px 0; font-size: 1.1em;">Разработка интеллектуального чат-бота для автоматизации консультаций по технологическому присоединению</h3>
</div>

**Задачи:**
- ✅ Внедрение гибридного поиска (семантический + лексический)
- ✅ Интеграция с векторной базой данных Qdrant
- ✅ Обеспечение аутентификации через Supabase
- ✅ Создание интуитивного веб-интерфейса на Vue.js 3
---

# 🔍 Обзор аналогов продукта

| Решение | RAG | Гибридный поиск | Отраслевая специализация |
|---------|-----|-----------------|---------------------------|
| **ИИ-ассистент Башкирэнерго** | ✓ | ✓ | ✓ Энергетика |
| Универсальные чат-боты | ✗ | ✗ | — |
| Базы знаний с поиском | ✗ | ✓ | — |

<div class="highlight-box">
<strong>Ключевое преимущество:</strong> комбинация RAG-архитектуры с 4-компонентным гибридным поиском, адаптированная специально для энергетической отрасли с учетом нормативной базы Башкирэнерго
---

# 👥 Функциональная модель (Use Case)

<div class="usecase-container">
  <div class="usecase-actor">
    <div class="actor-icon">👤</div>
    <div><strong>Клиент</strong></div>
  </div>
  <div class="usecase-system">
    <div style="text-align: center; margin-bottom: 10px; font-weight: 700; color: var(--primary);">Система ИИ-ассистента</div>
    <div class="usecase-item">Отправка запроса по тех. присоединению</div>
    <div class="usecase-item">Получение ответа с источниками</div>
    <div class="usecase-item">Просмотр истории чатов</div>
    <div class="usecase-item">Оценка качества ответа</div>
  </div>
---

# 🗃️ Логическая модель базы данных

<div class="er-diagram">
  <div class="er-table">
    <div class="er-header">USERS</div>
    <div class="er-fields">
      <div>uuid id PK</div>
      <div>string email</div>
      <div>string encrypted_password</div>
      <div>jsonb raw_user_meta_data</div>
      <div>timestamp created_at</div>
    </div>
  </div>
  <div class="er-table">
    <div class="er-header">CHAT_SESSIONS</div>
    <div class="er-fields">
      <div>uuid id PK</div>
      <div>uuid user_id FK</div>
      <div>string title</div>
      <div>timestamp created_at</div>
      <div>timestamp updated_at</div>
    </div>
  </div>
  <div class="er-table">
    <div class="er-header">MESSAGES</div>
    <div class="er-fields">
      <div>uuid id PK</div>
      <div>uuid session_id FK</div>
      <div>string role</div>
      <div>text content</div>
      <div>jsonb sources</div>
      <div>timestamp created_at</div>
    </div>
  </div>
  <div class="er-table">
    <div class="er-header">FEEDBACK</div>
    <div class="er-fields">
      <div>uuid id PK</div>
      <div>uuid message_id FK</div>
      <div>uuid user_id FK</div>
      <div>string rating</div>
      <div>timestamp created_at</div>
    </div>
  </div>
</div>

<div class="er-relationships">
<strong>Связи:</strong> USERS → CHAT_SESSIONS → MESSAGES → FEEDBACK | Supabase Auth + PostgreSQL
---

# 🏗️ UML диаграмма классов

<div class="class-diagram">
  <div class="class-box">
    <div class="class-header">SearchAgent</div>
    <div class="class-methods">
      <div>+ generateSearchQueries()</div>
      <div>+ searchDocuments()</div>
      <div>+ rankResults()</div>
    </div>
  </div>
  <div class="class-box">
    <div class="class-header">ResponseAgent</div>
    <div class="class-methods">
      <div>+ generateResponse()</div>
      <div>+ extractSources()</div>
      <div>+ formatAnswer()</div>
    </div>
  </div>
  <div class="class-box">
    <div class="class-header">SearchTool</div>
    <div class="class-methods">
      <div>+ hybridSearch()</div>
      <div>+ normalizeBM25()</div>
      <div>+ calculateWeights()</div>
    </div>
  </div>
  <div class="class-box">
    <div class="class-header">ChatService</div>
    <div class="class-methods">
      <div>+ handleQuery()</div>
      <div>+ streamResponse()</div>
      <div>+ saveSession()</div>
    </div>
  </div>
  <div class="class-box">
    <div class="class-header">AuthService</div>
    <div class="class-methods">
      <div>+ login()</div>
      <div>+ register()</div>
      <div>+ validateToken()</div>
    </div>
  </div>
  <div class="class-box">
    <div class="class-header">EmbeddingService</div>
    <div class="class-methods">
      <div>+ embedText()</div>
      <div>+ getEmbeddings()</div>
      <div>+ connectQdrant()</div>
    </div>
  </div>
---

# 🔄 Жизненный цикл ПО

<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-dot">1</div>
    <div class="timeline-label"><strong>Анализ</strong><br>требований</div>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot">2</div>
    <div class="timeline-label"><strong>Проекти-</strong><br>рование</div>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot">3</div>
    <div class="timeline-label"><strong>Раз-</strong><br>работка</div>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot">4</div>
    <div class="timeline-label"><strong>Тести-</strong><br>рование</div>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot">5</div>
    <div class="timeline-label"><strong>Деплой</strong><br>и запуск</div>
  </div>
  <div class="timeline-item">
    <div class="timeline-dot">6</div>
    <div class="timeline-label"><strong>Под-</strong><br>держка</div>
  </div>
</div>

<div class="highlight-box">
<strong>Модель:</strong> Итеративная разработка с непрерывным циклом обратной связи
</div>

---

# 🧮 Модель векторной базы данных

<div class="two-column">
  <div class="card">
    <h3 style="color: var(--primary); margin-top: 0;">Коллекция Qdrant</h3>
    <p><strong>Имя:</strong> <code>BASHKIR_ENERGO_PERPLEXITY</code></p>
    <p><strong>Модель:</strong> perplexity/pplx-embed-v1-4b</p>
    <p><strong>Размерность:</strong> 2560</p>
    <p><strong>Расстояние:</strong> Cosine similarity</p>
    <p><strong>Индекс:</strong> HNSW</p>
  </div>
  <div class="card">
    <h3 style="color: var(--primary); margin-top: 0;">Payload структура</h3>
    <ul style="font-size: 0.9em;">
      <li><code>content</code> — текст документа</li>
      <li><code>summary</code> — краткое содержание</li>
      <li><code>hypothetical_questions</code></li>
      <li><code>source</code> — источник</li>
      <li><code>metadata</code></li>
    </ul>
  </div>
</div>

**Компоненты гибридного поиска:**
- Semantic (pref): **40%** — summary + content
- Semantic (hype): **30%** — hypothetical questions
- Lexical (BM25): **20%** — лексический поиск
---

# 🏛️ Архитектура системы

<div class="arch-diagram">
  <div class="arch-node">🌐 Browser (Vue.js 3)</div>
  <div class="arch-arrow">↓</div>
  <div class="arch-node primary">🔀 Nginx (Port 80)</div>
  <div class="arch-arrow">↓</div>
  <div class="arch-node secondary">⚡ FastAPI Backend (Port 8880)</div>
  <div class="arch-arrow">↓</div>
  <div class="arch-services">
    <div class="arch-node">🗄️ Supabase<br><small>PostgreSQL + Auth</small></div>
    <div class="arch-node">🔍 Qdrant<br><small>Port 6333</small></div>
    <div class="arch-node">🤖 RouterAI API<br><small>LLM + Embeddings</small></div>
  </div>
---

# 🔧 Компоненты системы

<div class="two-column">
  <div>
    <div class="card">
      <h3 style="color: var(--primary); margin-top: 0;">🔍 Search Agent</h3>
      <p style="font-size: 0.9em;">Генерация поисковых запросов, гибридный поиск, ранжирование результатов</p>
    </div>
    <div class="card">
      <h3 style="color: var(--primary); margin-top: 0;">🤖 Response Agent</h3>
      <p style="font-size: 0.9em;">Генерация ответа через LLM, извлечение источников, форматирование</p>
    </div>
    <div class="card">
      <h3 style="color: var(--primary); margin-top: 0;">🛠️ Search Tool</h3>
      <p style="font-size: 0.9em;">4-компонентный поиск: pref, hype, contextual, BM25</p>
    </div>
  </div>
  <div>
    <div class="card">
      <h3 style="color: var(--primary); margin-top: 0;">💬 Chat Store</h3>
      <p style="font-size: 0.9em;">Управление состоянием чата, история сессий, streaming</p>
    </div>
    <div class="card">
      <h3 style="color: var(--primary); margin-top: 0;">🔐 Auth Service</h3>
      <p style="font-size: 0.9em;">JWT аутентификация, регистрация, вход через Supabase</p>
    </div>
    <div class="card">
      <h3 style="color: var(--primary); margin-top: 0;">📐 Embedding Service</h3>
      <p style="font-size: 0.9em;">Векторизация текста, подключение к Qdrant</p>
    </div>
  </div>
---

# 🔄 Пайплайн обработки данных

<div class="pipeline">
  <div class="pipeline-step">1. Запрос клиента</div>
  <div class="pipeline-arrow">→</div>
  <div class="pipeline-step">2. Генерация запросов</div>
  <div class="pipeline-arrow">→</div>
  <div class="pipeline-step">3. Гибридный поиск</div>
  <div class="pipeline-arrow">→</div>
  <div class="pipeline-step">4. Ранжирование</div>
  <div class="pipeline-arrow">→</div>
  <div class="pipeline-step">5. Генерация ответа</div>
  <div class="pipeline-arrow">→</div>
  <div class="pipeline-step">6. Streaming</div>
</div>

<div class="highlight-box">
<strong>Формула гибридного поиска:</strong><br>
<code>hybrid = 0.4 × pref + 0.3 × hype + 0.1 × contextual + 0.2 × BM25</code><br><br>
<strong>BM25 нормализация:</strong> <code>score / max_score</code>
---

# 🛠️ Инструменты разработки

<div class="two-column">
  <div>
    <h3 style="color: var(--primary); margin-top: 0;">Backend</h3>
    <ul style="font-size: 0.95em;">
      <li>Python 3.11</li>
      <li>FastAPI</li>
      <li>Uvicorn</li>
      <li>Pydantic</li>
    </ul>
    
    <h3 style="color: var(--primary);">Frontend</h3>
    <ul style="font-size: 0.95em;">
      <li>Vue.js 3</li>
      <li>Vite</li>
      <li>Pinia</li>
      <li>Vue Router</li>
    </ul>
  </div>
  <div>
    <h3 style="color: var(--primary); margin-top: 0;">Базы данных</h3>
    <ul style="font-size: 0.95em;">
      <li>Supabase</li>
      <li>PostgreSQL</li>
      <li>Qdrant</li>
      <li>pgvector</li>
    </ul>
    
    <h3 style="color: var(--primary);">Инфраструктура</h3>
    <ul style="font-size: 0.95em;">
      <li>Docker</li>
      <li>Docker Compose</li>
      <li>Nginx</li>
      <li>RouterAI API</li>
    </ul>
  </div>
</div>

# 📅 Календарь разработки

<div class="gantt-chart">
  <div class="gantt-row">
    <div class="gantt-label">Анализ и проектирование</div>
    <div class="gantt-bar-container">
      <div class="gantt-bar phase1" style="flex: 2;"></div>
      <div class="gantt-bar" style="flex: 6; background: transparent;"></div>
    </div>
  </div>
  <div class="gantt-row">
    <div class="gantt-label">Разработка backend</div>
    <div class="gantt-bar-container">
      <div class="gantt-bar" style="flex: 2; background: transparent;"></div>
      <div class="gantt-bar phase2" style="flex: 3;"></div>
      <div class="gantt-bar" style="flex: 3; background: transparent;"></div>
    </div>
  </div>
  <div class="gantt-row">
    <div class="gantt-label">Разработка frontend</div>
    <div class="gantt-bar-container">
      <div class="gantt-bar" style="flex: 3; background: transparent;"></div>
      <div class="gantt-bar phase3" style="flex: 2;"></div>
      <div class="gantt-bar" style="flex: 3; background: transparent;"></div>
    </div>
  </div>
  <div class="gantt-row">
    <div class="gantt-label">Интеграция и тестирование</div>
    <div class="gantt-bar-container">
      <div class="gantt-bar" style="flex: 5; background: transparent;"></div>
      <div class="gantt-bar phase1" style="flex: 2;"></div>
      <div class="gantt-bar" style="flex: 1; background: transparent;"></div>
    </div>
  </div>
  <div class="gantt-row">
    <div class="gantt-label">Деплой и запуск</div>
    <div class="gantt-bar-container">
      <div class="gantt-bar" style="flex: 7; background: transparent;"></div>
      <div class="gantt-bar phase2" style="flex: 1;"></div>
    </div>
  </div>
  <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 0.75em; color: var(--gray);">
    <span style="flex: 1;"></span>
    <span style="flex: 1; text-align: center;">Янв</span>
    <span style="flex: 1; text-align: center;">Фев</span>
    <span style="flex: 1; text-align: center;">Мар</span>
    <span style="flex: 1; text-align: center;">Апр</span>
    <span style="flex: 1; text-align: center;">Май</span>
    <span style="flex: 1; text-align: center;">Июн</span>
    <span style="flex: 1; text-align: center;">Июл</span>
    <span style="flex: 1; text-align: center;">Авг</span>
  </div>
</div>

**Ключевые вехи:** ✅ Прототип RAG • ✅ Интеграция с Qdrant • ✅ Запуск production

---
<!-- class: light-bg -->
# 🏆 Основные результаты

<div class="stats-grid">
  <div class="stat-card">
    <span class="stat-number">85%</span>
    <span class="stat-label">Снижение нагрузки на операторов</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">< 3 сек</span>
    <span class="stat-label">Время генерации ответа</span>
  </div>
  <div class="stat-card">
    <span class="stat-number">95%</span>
    <span class="stat-label">Точность ответов</span>
  </div>
</div>

**Дополнительные достижения:**
- ✅ Реализован гибридный поиск с 4 компонентами
- ✅ Интеграция с существующей инфраструктурой Qdrant
- ✅ Streaming-генерация ответов через SSE
- ✅ Полная аутентификация и авторизация
- ✅ История чатов с возможностью поиска
- ✅ Система обратной связи (like/dislike)

---
<!-- class: lead -->
# 🎉 Благодарю за внимание!

## ИИ-ассистент по технологическому присоединению готов к промышленной эксплуатации

---

**Контакты:** almaz_sabitov04@mail.ru  
**2026**
