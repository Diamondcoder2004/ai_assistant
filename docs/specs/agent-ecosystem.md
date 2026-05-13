# Agent Ecosystem — OpenCode Configuration Guide

Дата: 2026-05-01
Версия конфигурации: финальная

---

## 1. Общая архитектура

```mermaid
graph TB
    subgraph User["Пользователь"]
        TUI["OpenCode TUI"]
    end

    subgraph Plugins["Плагины OpenCode"]
        PL["@plannotator/opencode<br/>Интерактивное ревью планов"]
        NF["@mohak34/opencode-notifier<br/>Уведомления + звуки"]
        MC["micode"]
        HV["opencode-hive"]
    end

    subgraph MCP["MCP-серверы"]
        C7["context7<br/>Контекстная документация"]
    end

    subgraph Agents["Глобальные агенты (8)"]
        BE["backend-dev<br/>DeepSeek V4 Pro"]
        FE["frontend-dev<br/>Kimi K2.6"]
        TW["technical-writer<br/>Qwen3.6 Plus"]
        CR["code-review<br/>DeepSeek V4 Flash"]
        SA["security-auditor<br/>Qwen3.6 Plus"]
        UA["ux-analyst<br/>DeepSeek V4 Flash"]
        DS["doc-specialist-go<br/>MiniMax M2.7"]
        RV["review<br/>DeepSeek V4 Flash"]
    end

    subgraph Skills["Глобальные скиллы (8)"]
        DD["diagram-drawio"]
        DM["diagram-mermaid"]
        MD["minimax-docx"]
        MP["minimax-pdf"]
        MX["minimax-xlsx"]
        PP["pptx-generator"]
        SB["supabase"]
        AB["agent-browser"]
    end

    subgraph Commands["Slash-команды (5)"]
        UX["/ux-review"]
        PA1["/plannotator-review"]
        PA2["/plannotator-annotate"]
        PA3["/plannotator-last"]
        PA4["/plannotator-archive"]
    end

    TUI -->|"вызов агента"| Agents
    TUI -->|"slash-команда"| Commands
    Agents -->|"Skill tool"| Skills
    Agents -->|"Task tool"| Agents
    Plugins -->|"расширяют"| TUI
    MCP -->|"данные"| TUI

    style User fill:#e1f5fe
    style Plugins fill:#fff3e0
    style MCP fill:#f3e5f5
    style Agents fill:#e8f5e9
    style Skills fill:#fce4ec
    style Commands fill:#ede7f6
```

---

## 2. Иерархия ролей

Экосистема работает по принципу **иерархического делегирования**. Не все агенты равны — есть разделение на роли верхнего уровня (оркестрация и принятие решений), доменные агенты (специалисты по направлениям) и вспомогательные subagents (разведка, планирование, исполнение).

### 2.1. Роли верхнего уровня

| Роль | Назначение | Кто вызывает |
|---|---|---|
| **Commander** | Senior engineer. Принимает решения, даёт добро на план, запускает исполнение, коммитит результат. Не пишет код напрямую — делегирует. | Пользователь напрямую |
| **Hive-master** | Гибридный планировщик + оркестратор. Определяет фазу проекта, подгружает нужные skills on-demand, синхронизирует tasks и worktrees. | Commander или автоматически при complex tasks |

**Commander** — это единственная роль, которая имеет право:
- одобрить или отклонить план перед имплементацией;
- создать коммит и смержить ветку;
- принять архитектурное решение при конфликте subagents.

**Hive-master** берёт на себя рутину оркестрации:
- создание фиче-бранчей и git worktrees;
- генерацию task-списка из plan.md;
- отслеживание статуса задач (pending → in-progress → completed);
- merge completed task branches.

### 2.2. Доменные агенты (globals)

Специалисты, привязанные к конкретным моделям и навыкам. Вызываются через `Task tool` с указанием `subagent_type`.

```mermaid
graph LR
    subgraph Backend["Бэкенд"]
        BE[("backend-dev<br/><b>DeepSeek V4 Pro</b><br/>read/write/edit/bash/grep/skill")]
    end
    subgraph Frontend["Фронтенд"]
        FE[("frontend-dev<br/><b>Kimi K2.6</b><br/>read/write/edit/grep")]
    end
    subgraph Review["Ревью и безопасность"]
        CR[("code-review<br/><b>DeepSeek V4 Flash</b><br/>read/grep")]
        SA[("security-auditor<br/><b>Qwen3.6 Plus</b><br/>read/grep")]
        RV[("review<br/><b>DeepSeek V4 Flash</b><br/>read/grep")]
    end
    subgraph Docs["Документация"]
        TW[("technical-writer<br/><b>Qwen3.6 Plus</b><br/>read/write/edit/grep/skill<br/>→ diagram-drawio<br/>→ diagram-mermaid")]
        DS[("doc-specialist-go<br/><b>MiniMax M2.7</b><br/>read/write/edit/bash/grep/skill<br/>→ minimax-docx/pdf/xlsx<br/>→ pptx-generator")]
    end
    subgraph UX["UX"]
        UA[("ux-analyst<br/><b>DeepSeek V4 Flash</b><br/>read")]
    end

    BE -.->|"skill: supabase"| SB[("supabase skill")]
    TW -.->|"skill: diagram"| DM[("diagram-drawio<br/>diagram-mermaid")]
    DS -.->|"skill: office"| OF[("minimax-*<br/>pptx-generator")]
```

| Агент | Модель | Инструменты | Навыки (skill) |
|---|---|---|---|
| `backend-dev` | `opencode-go/deepseek-v4-pro` | Read, Write, Edit, Bash, Glob, Grep, skill | `supabase` |
| `frontend-dev` | `opencode-go/kimi-k2.6` | Read, Write, Edit, Grep | — |
| `technical-writer` | `opencode-go/qwen3.6-plus` | Read, Write, Edit, Glob, Grep, skill | `adk-diagram-drawio`, `adk-diagram-mermaid` |
| `code-review` | `opencode-go/deepseek-v4-flash` | Read, Grep | — |
| `security-auditor` | `opencode-go/qwen3.6-plus` | Read, Grep | — |
| `ux-analyst` | `opencode-go/deepseek-v4-flash` | Read | — |
| `doc-specialist-go` | `opencode-go/minimax-m2.7` | Read, Write, Edit, Bash, Glob, Grep, skill | `minimax-docx`, `minimax-pdf`, `minimax-xlsx`, `pptx-generator` |
| `review` | `opencode-go/deepseek-v4-flash` | Read, Grep | — |

### 2.3. Subagents / Micode-агенты

Вспомогательные агенты, которые вызываются изнутри сессии (через `Task` или `spawn_agent`). Они не привязаны к конкретной LLM-модели в конфиге — их поведение определяется системным промптом и контекстом вызова.

**Типы агентов:**

| Тип | Значение | Кто вызывает |
|---|---|---|
| **Primary** | Агент, который пользователь вызывает **напрямую** (не через другого агента). Работает в интерактиве с пользователем. | Пользователь или Commander |
| **Subagent** | Вспомогательный агент, запускаемый **изнутри сессии** другим агентом. Не имеет прямого контакта с пользователем. | Commander, executor, hive-master |
| **Hive** | Специализированный вспомогательный агент для работы с git worktrees, task-менеджментом и восстановлением после конфликтов. | Hive-master |

| Агент | Тип | Назначение | Когда вызывать |
|---|---|---|---|
| **brainstormer** | Primary | Интерактивное проектирование фичи. Задаёт уточняющие вопросы, исследует требования, порождает design document. | Требования неясны; нужен design перед планом |
| **planner** | Subagent | Создаёт детальный implementation plan (`plan.md`) на основе design или чётких требований. | Есть design или ясная задача |
| **executor** | Subagent | Исполняет approved plan. Сам запускает `implementer` → `reviewer` в цикле до одобрения или эскалации. | План одобрен Commander |
| **implementer** | Subagent | Микро-исполнитель. Создаёт **один** файл + его тест, запускает verification. | Внутри executor |
| **reviewer** | Subagent | Микро-ревьювер. Проверяет, что файл соответствует плану и тест проходит. | Внутри executor |
| **codebase-locator** | Subagent | Находит **где** лежат файлы по паттернам (`src/**/*.ts`, класс `Foo`). | Нужен поиск по имени/паттерну |
| **codebase-analyzer** | Subagent | Объясняет **как** работает код. Даёт точные `file:line` ссылки. | Нужно понять логику модуля |
| **pattern-finder** | Subagent | Ищет существующие паттерны и примеры для подражания. | Нужно делать «как везде в проекте» |
| **ledger-creator** | Subagent | Создаёт и обновляет continuity-ledgers (`thoughts/ledgers/`) для сохранения контекста между сессиями. | Контекст переполнен или сессия завершается |
| **artifact-searcher** | Subagent | Ищет в прошлых планах, леджерах и handoffs похожие решения. | Повторяющаяся проблема |
| **scout-researcher** | Subagent | Исследует кодовую базу + внешнюю документацию параллельно. | Нужен быстрый обзор |
| **explore** | Subagent | Быстрый обход кодовой базы. Поиск файлов, ключевых слов, ответы на вопросы «как устроен X?». | Первичное знакомство с проектом |
| **bootstrapper** | Subagent | Анализирует запрос и создаёт exploration branches для **octto**-brainstorming. | Перед интерактивным brainstorm |
| **probe** | Subagent | Оценивает ответы веток octto и решает — задать ещё вопрос или завершить. | Внутри octto-сессии |
| **hive-helper** | Hive | Runtime-ассистент для восстановления после merge-конфликтов, уточнения состояния, ручных доработок. | Что-то пошло не так у hive-master |

### 2.4. Octto — интерактивный brainstorming

> **Важно:** Octto — это **не агент**. Это **подсистема / движок** внутри TUI, которая открывает интерактивную сессию в браузере. Агенты, связанные с octto — это `bootstrapper` (Subagent) и `probe` (Subagent), но сам Octto — это инфраструктура для структурированного мозгового штурма.

**Octto** открывает в браузере интерактивную сессию с ветвями (branches) исследования. Вместо того чтобы агент задавал уточняющие вопросы текстом в чате, пользователь отвечает на структурированные вопросы (pick_one, rank, ask_text, show_diff и др.) прямо в UI.

```mermaid
sequenceDiagram
    actor User
    participant TUI as OpenCode TUI
    participant BS as bootstrapper
    participant Octto as Octto Engine
    participant PR as probe

    User->>TUI: Запрос brainstorm
    TUI->>BS: Анализ запроса
    BS-->>TUI: Список ветвей (branches)
    TUI->>Octto: create_brainstorm
    Octto-->>User: Интерактивные вопросы в браузере
    User->>Octto: Ответы
    Octto->>PR: Оценка ответов
    PR-->>Octto: Завершить или углубиться
    Octto-->>TUI: Итоговый summary
```

**Ключевые компоненты octto:**

| Компонент | Назначение |
|---|---|
| `create_brainstorm` | Создаёт сессию с набором exploration branches — каждая ветка исследует свой аспект проблемы |
| `start_session` | Открывает браузер с первым вопросом |
| `bootstrapper` | Анализирует запрос пользователя и формирует начальные ветки для brainstorming |
| `probe` | Оценивает ответы пользователя в каждой ветке и решает: задать уточняющий вопрос или считать ветку завершённой |
| `await_brainstorm_complete` | Блокирует выполнение до тех пор, пока пользователь не пройдёт все ветки |
| `end_brainstorm` | Закрывает сессию и формирует финальный summary |

**Типы вопросов в octto:** `pick_one`, `pick_many`, `confirm`, `rank`, `rate`, `ask_text`, `ask_image`, `ask_file`, `ask_code`, `show_diff`, `show_plan`, `show_options`, `review_section`, `thumbs`, `emoji_react`, `slider`.

#### Build и Plan — куда они делись?

В ранних версиях micode существовали роли `Build` и `Plan` как самостоятельные агенты. Они не исчезли, а **эволюционировали в режимы работы**:

- **Plan** стал **plan mode** (и `planner` subagent). Теперь это не отдельный агент, а **режим**: в нём запрещены все edit-инструменты — только исследование и написание `plan.md`.
- **Build** стал **build** (default agent) — базовый режим выполнения инструкций. Вся функциональность «строительства» распалась на специализированных агентов: `implementer` пишет файл, `executor` оркестрирует, `hive-master` управляет ветками.
- **[SUPERMEMORY — удалён]** Ранее присутствовал как плагин (`opencode-supermemory`) + MCP-сервер (`supermemory`). Полностью удалён из системы: конфиги, плагин, MCP, переменные окружения, файлы и команды. Не используется.

---

## 3. Плагины

```mermaid
graph TD
    subgraph PluginConfig["opencode.jsonc — plugin: [...]"]
        P1["@plannotator/opencode@latest"]
        P2["@mohak34/opencode-notifier@latest"]
        P3["micode"]
        P4["opencode-hive"]
    end

    P1 -->|"предоставляет"| CMD1["/plannotator-review"]
    P1 --> CMD2["/plannotator-annotate"]
    P1 --> CMD3["/plannotator-last"]
    P1 --> CMD4["/plannotator-archive"]

    P2 -->|"уведомления"| NT["звуки + toast<br/>на: permission, finish, error"]
    P3 -->|"subagent framework"| MICODE["micode агенты<br/>brainstormer, executor,<br/>planner, reviewer..."]
    P4 -->|"hive orchestration"| HIVE["Hive-master<br/>worktrees, tasks,<br/>git branches"]
```

| Плагин | Назначение | Команды |
|---|---|---|
| `@plannotator/opencode` | Интерактивное ревью планов в браузере | `/plannotator-review`, `*-annotate`, `*-last`, `*-archive` |
| `@mohak34/opencode-notifier` | Системные уведомления + звуки | — (автоматически) |
| `micode` | Расширение TUI — предоставляет subagent-фреймворк (brainstormer, planner, executor, implementer, reviewer, codebase-locator и др.) | — |
| `opencode-hive` | Оркестрация через Hive-master: git worktrees, task management, branch lifecycle | — |

---

## 4. MCP-серверы

```mermaid
graph LR
    subgraph MCPConfig["opencode.jsonc — mcp: {...}"]
        C7["context7<br/>type: local<br/>npx @upstash/context7-mcp"]
    end

    C7 -->|"документация библиотек"| DOCS["Context7 API"]
```

| MCP | Тип | Назначение |
|---|---|---|
| `context7` | `local` (npx) | Контекстная подгрузка документации библиотек |

---

## 5. Глобальные скиллы

```mermaid
graph TD
    subgraph GlobalSkills["C:\Users\almaz\.config\opencode\skills\"]
        S1["diagram-drawio<br/>draw.io XML + diagramkit"]
        S2["diagram-mermaid<br/>Mermaid 21 type ref"]
        S3["minimax-docx<br/>OpenXML SDK (.NET)"]
        S4["minimax-pdf<br/>token-based design"]
        S5["minimax-xlsx<br/>Excel/spreadsheets"]
        S6["pptx-generator<br/>PptxGenJS"]
        S7["supabase<br/>безопасные операции с БД"]
        S8["agent-browser<br/>браузерная автоматизация"]
    end

    S1 -->|"использует"| TW["technical-writer"]
    S2 -->|"использует"| TW
    S3 -->|"использует"| DS["doc-specialist-go"]
    S4 -->|"использует"| DS
    S5 -->|"использует"| DS
    S6 -->|"использует"| DS
    S7 -->|"использует"| BE["backend-dev"]
    S8 -.->|"commander (bash)"| CMD["Commander"]

    style GlobalSkills fill:#fce4ec
```

| Скилл | Тип | Привязка к агенту |
|---|---|---|
| `diagram-drawio` | draw.io схемы (сети, архитектура, BPMN) | `technical-writer` |
| `diagram-mermaid` | Mermaid диаграммы (21 тип) | `technical-writer` |
| `minimax-docx` | DOCX создание/редактирование | `doc-specialist-go` |
| `minimax-pdf` | PDF создание/форматирование | `doc-specialist-go` |
| `minimax-xlsx` | Excel/CSV операции | `doc-specialist-go` |
| `pptx-generator` | PowerPoint презентации | `doc-specialist-go` |
| `supabase` | Безопасные операции с БД | `backend-dev` |
| `agent-browser` | Браузерная автоматизация (Vercel Labs) | `Commander` (через bash) |

### 5.1. Проектные скиллы (matt-*)

Хранятся в `D:\ai_assistant\.opencode\skills\`. Используются по ситуации:

| Скилл | Назначение | Когда применять | Кто загружает |
|---|---|---|---|
| `matt-grill-me` | Стресс-тест плана/дизайна | Пользователь просит «проверь план», «grill me» | Commander / brainstormer |
| `matt-improve-architecture` | Рефакторинг, углубление модулей | Улучшение архитектуры, связности | Commander + codebase-analyzer |
| `matt-tdd` | TDD: red-green-refactor | Разработка через тестирование | executor / implementer |
| `matt-to-issues` | План → GitHub issues | Разбить работу на задачи | planner |
| `matt-to-prd` | Контекст → PRD → GitHub issue | Создание PRD из обсуждения | technical-writer |
| `matt-ubiquitous-language` | Единый доменный язык, глоссарий | Доменное моделирование, DDD | technical-writer |

### 5.2. Legacy skills — не использовать

| Скилл | Причина |
|---|---|
| `doc-specialist` | Заменён на `doc-specialist-go` + `minimax-*`. В конфиге агента явно запрещён. |

---

## 6. Slash-команды

```mermaid
graph LR
    subgraph Slash["/команды в TUI"]
        UXR["/ux-review &lt;file&gt;"]
        PLR["/plannotator-review"]
        PLA["/plannotator-annotate"]
        PLL["/plannotator-last"]
        PLARC["/plannotator-archive"]
    end

    UXR -->|"вызывает"| AG["ux-analyst агент<br/>Nielsen heuristics"]
    PLR -->|"открывает"| BR["браузер: ревью плана"]
    PLA -->|"открывает"| BR2["браузер: аннотация"]
    PLL -->|"открывает"| BR3["браузер: последнее сообщение"]
```

| Команда | Описание | Источник |
|---|---|---|
| `/ux-review <файл>` | UX-анализ по эвристикам Нильсена | `commands/ux-review.md` |
| `/plannotator-review` | Интерактивное ревью кода/плана | `@plannotator/opencode` |
| `/plannotator-annotate` | Аннотирование файла/URL | `@plannotator/opencode` |
| `/plannotator-last` | Аннотировать последний ответ | `@plannotator/opencode` |
| `/plannotator-archive` | Архив планов | `@plannotator/opencode` |

---

## 7. Поток работы агента

```mermaid
sequenceDiagram
    actor User
    participant TUI as OpenCode TUI
    participant CMD as Commander
    participant HM as Hive-master
    participant Agent as Агент (Domain)
    participant Sub as Subagent
    participant Skill as Skill tool
    participant MCP as MCP-сервер
    participant Plugin as Плагины

    User->>TUI: /команда или запрос
    TUI->>CMD: Dispatch (model + tools)

    alt Требуется оркестрация
        CMD->>HM: Создать worktree + tasks
        HM-->>CMD: Tasks synced
    end

    alt Делегирование subagent
        CMD->>Sub: Task tool (subagent_type)
        Sub-->>CMD: Результат
    else Прямое выполнение
        CMD->>Agent: Вызов доменного агента
        Agent-->>CMD: Результат
    end

    alt Есть привязанный skill
        Agent->>Skill: Загрузить skill
        Skill-->>Agent: Инструкции
    end

    Agent->>MCP: context7
    MCP-->>Agent: Контекст

    Agent->>Plugin: Уведомления (notifier)
    Plugin-->>Agent: Звук/toast

    Agent->>Agent: Выполнение задачи
    Agent-->>CMD: Результат
    CMD-->>TUI: Результат
    TUI-->>User: Ответ
```

---

## 8. Конфигурационные файлы

| Файл | Расположение | Назначение |
|---|---|---|
| `opencode.jsonc` | `C:\Users\almaz\.config\opencode\` | Глобальная конфигурация: плагины, MCP |
| `opencode.json` | `D:\ai_assistant\` | Проектная конфигурация: инструкции |
| `opencode-notifier.json` | `C:\Users\almaz\.config\opencode\` | Настройки уведомлений |
| `agents/*.md` | `C:\Users\almaz\.config\opencode\agents\` | 8 субагентов |
| `commands/*.md` | `C:\Users\almaz\.config\opencode\commands\` | 8 slash-команд |
| `skills/*/` | `C:\Users\almaz\.config\opencode\skills\` | 8 глобальных скиллов + 6 проектных |
| `graph.json` | `C:\Users\almaz\.config\opencode\` | Граф знаний (943 узла) |

---

## 9. Переменные окружения

Нет дополнительных переменных окружения. Все настройки — в `opencode.jsonc` (MCP, plugin) и `micode.jsonc` (agents, skills routing).
