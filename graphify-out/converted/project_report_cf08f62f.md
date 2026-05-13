<!-- converted from project_report.docx -->

# AI-ассистент для Башкирэнерго
Проект D:\ai_assistant\ai_assistant
## 1. Название и цель проекта
RAG-чат-бот для поддержки технологического присоединения к электросетям (ТПП) в компании Башкирэнерго.
Цель: Автоматизация ответов на вопросы клиентов по трём направлениям:
- ЛК — Личный кабинет (операции с лицевым счётом)
- ДУ — Дополнительные услуги (платные сервисы)
- ТПП — Технологическое присоединение (основной процесс)
## 2. Архитектура
### 2.1 Компоненты системы
### 2.2 Пайплайн агентов
User Query → SearchAgent → Hybrid Search (Qdrant + BM25) → ResponseAgent → LLM Response + Sources
### 2.3 Hybrid Search
Четыре компонента поиска с весами (сумма = 1.0):
- PREF — 0.4 (предпочтения пользователя)
- HYPE — 0.3 (гипербола)
- LEXICAL — 0.2 (лейкемия)
- CONTEXTUAL — 0.1 (контекст)
## 3. Стек технологий
## 4. Ключевые директории
## 5. Конвенции и ограничения
### 5.1 Критические ограничения
- Точка входа бэкенда: api.api:app (НЕ main.py)
- BM25 нормализация: score / max_score (классическая, без tanh/softmax)
- Промпты: заморожены в backend/prompts/ — не менять стиль написания
- Кодировка: UTF-8 для кириллицы; CSV с BOM (utf-8-sig)
- Supabase: двойная роль — JWT auth + хранилище истории чата
### 5.2 Конфигурация
Для запуска: скопировать .env.example → .env и заполнить:
- ROUTERAI_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- SUPABASE_JWT_SECRET
### 5.3 Команды
Docker: docker-compose up -d --build / docker-compose down
Backend локально: cd backend && uvicorn api.api:app --reload --host 0.0.0.0 --port 8880
Frontend локально: cd frontend && npm run dev
Тесты бэкенда: cd backend && pytest
Тесты фронтенда: cd frontend && npm run test:unit && npm run lint
### 5.4 Доменные категории
ФЛ — Физическое лицо | ИП — Индивидуальный предприниматель | ЮЛ — Юридическое лицо
Критерии оценки judge: relevance, completeness, helpfulness, clarity, hallucination_risk, context_recall, faithfulness, currency, binary_correctness, overall_score
### 5.5 Определение успеха
Корректный ответ = ответ модели совпадает с ожидаемой процедурой + правильная терминология + соблюдение доменных ограничений (категории ФЛ/ИП/ЮЛ, лимиты мощности, классы напряжения) + отсутствие галлюцинаций.
| Компонент | Описание |
| --- | --- |
| Vue 3 SPA | Фронтенд на Vue 3 + Vite + Pinia + Tailwind |
| nginx :80 | Обслуживание статических файлов фронтенда |
| nginx :8877 | Проксирование API-запросов к бэкенду |
| FastAPI :8880 | Бэкенд-сервер (agents, tools, prompts) |
| Qdrant :6333 | Векторная база данных (коллекция BASHKIR_ENERGO_PERPLEXITY) |
| Supabase :8000 | JWT-авторизация + PostgreSQL (история чата) |
| RouterAI API | LLM (inception/mercury-2) + embeddings (pplx-embed-v1-4b) |
| Слой | Технологии |
| --- | --- |
| Backend | Python 3.11+, FastAPI (api.api:app) |
| Frontend | Vue 3, Vite, Pinia, Tailwind |
| Database | Supabase (PostgreSQL) |
| Vector DB | Qdrant (port 6333) |
| LLM | RouterAI: inception/mercury-2 |
| Embeddings | perplexity/pplx-embed-v1-4b |
| Judge | deepseek/deepseek-v3.2 |
| Директория | Назначение |
| --- | --- |
| backend/ | FastAPI-приложение — agents, tools, prompts, config |
| backend/agents/ | SearchAgent, ResponseAgent, QueryGenerator |
| backend/api/ | REST endpoints: /query, /query/stream, /history, /feedback |
| backend/prompts/ | Системные промпты (ЗАБЛОКИРОВАНЫ — не менять стиль) |
| frontend/ | Vue 3 SPA — чат-интерфейс, история, профиль |
| api_benchmarks/ | CSV с результатами бенчмарков (оценки judge) |
| new_data/ | Датасеты бенчмарков: вопрос + ожидаемый ответ + source |
| practice/ | Тестовые документы и экспертные ревью (.docx) |
| docs/specs/ | Долговечные спецификации проекта |
| .opencode/ | OpenCode-слой: agents, skills |
| scripts/ | Утилиты (конвертация PDF, генерация слайдов) |