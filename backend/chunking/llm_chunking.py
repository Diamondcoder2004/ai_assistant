#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Асинхронный обогатитель чанков с автоматическим восстановлением JSON,
логированием ошибок, добавлением метаданных и few-shot примерами из CSV.
Поддерживает докачку: обрабатываются только новые или ранее не удавшиеся чанки.
"""
import os
import re
import json
import asyncio
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
from openai import AsyncOpenAI
from tqdm import tqdm
PROCESSED_FILES = [
    #"1. ФЗ 35 (28.04.2025).md",
    "2. 861 (28.04.2025).md",
    "3. 1178 Основы ценообразования.md",
    "4. 490_22 Методические указания.md",
    #"5. Постановление ГКТ РБ №508 от 29.11.2024 ставки ТП и выпадающие 2025.md",

    #"8. 186 О единых стандартах обслуживания.md",
    "9. 442 О ФУНКЦИОНИРОВАНИИ РОЗНИЧНЫХ РЫНКОВ.md",

    "6. Информационное письмо по платным услугам.md",
    "6.2 Заявление на платные услуги ЮЛ.md",
    "22.Документ из сайта, особенности тех приса.md",
    "21. Памятка свыше 150 кВт.md",
    "20. Памятка до 150 кВт.md"

]
# ================= НАСТРОЙКИ =================
CHUNKS_DIR = Path("chunks_universal")                 # исходные чанки (подпапка legal)
OUTPUT_DIR = Path("chechov")        # результаты
LOGS_DIR = Path("logs")                            # логи
RAW_DIR = Path("raw_responses_v2")                 # сырые ответы
CSV_PATH = Path("../faq_question.csv")              # few-shot примеры

# Создаём папки
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# API настройки
API_KEY = "sk-5ArynRNUi11lFMyvtj5NBv4bFPS0xBs0"
BASE_URL = "https://routerai.ru/api/v1"
MODEL_NAME = "qwen/qwen3.5-flash-02-23"
TIMEOUT = 600
MAX_TOKENS = 80_000
TEMPERATURE = 0.15
MAX_RETRIES = 5
BASE_DELAY = 2
MAX_CONCURRENT_REQUESTS = 3

CHUNK_SEPARATOR = "\n\n---CHUNK---\n\n"
CATEGORY = "legal"

# ================= ЗАГРУЗКА FEW-SHOT ПРИМЕРОВ =================
few_shot_examples = []
if CSV_PATH.exists():
    try:
        df = pd.read_csv(CSV_PATH)
        if "Вопрос" in df.columns:
            few_shot_examples = df["Вопрос"].dropna().astype(str).tolist()[:5]
            logging.info(f"Загружено {len(few_shot_examples)} few-shot примеров из {CSV_PATH}")
        else:
            logging.warning("CSV не содержит столбца 'Вопрос', few-shot отключён")
    except Exception as e:
        logging.error(f"Ошибка загрузки CSV: {e}")
else:
    logging.warning(f"Файл {CSV_PATH} не найден, few-shot отключён")

# ================= НАСТРОЙКА ЛОГГЕРА =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "processing.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

FAILED_LOG = LOGS_DIR / "failed_chunks.json"

# ================= ИНИЦИАЛИЗАЦИЯ КЛИЕНТА =================
client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT)
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


# ================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =================
def generate_parent_chunk_id(source_file: str, chunk_text: str) -> str:
    """Генерирует идентификатор родительского чанка (первые 12 символов md5)."""
    hash_input = f"{source_file}:{chunk_text[:100]}".encode()
    return hashlib.md5(hash_input).hexdigest()[:12]


def clean_json_string(text: str) -> str:
    """Очистка JSON от markdown-обёрток и управляющих символов."""
    if not text:
        return text
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
    return text


def repair_json(raw: str) -> Optional[List[Dict]]:
    """Пытается восстановить JSON из сырого ответа."""
    try:
        cleaned = clean_json_string(raw)
        if not cleaned:
            return None
        if not (cleaned.startswith('[') or cleaned.startswith('{')):
            match = re.search(r'(\[.*\]|\{.*\})', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)
            else:
                return None
        # Экранируем все обратные слеши, кроме разрешённых
        cleaned = re.sub(r'\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', cleaned)
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
    except Exception as e:
        logger.debug(f"repair_json не удался: {e}")
    return None


def save_raw_response(content: str, source_file: str, parent_id: str, attempt: int):
    """Сохраняет сырой ответ модели."""
    filename = f"{source_file}_{parent_id}_attempt{attempt}.txt"
    path = RAW_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def log_failure(source_file: str, parent_id: str, raw_response: str):
    """Записывает информацию о полностью провалившемся чанке."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source_file": source_file,
        "parent_chunk_id": parent_id,
        "raw_response_preview": raw_response[:500]
    }
    if FAILED_LOG.exists():
        with open(FAILED_LOG, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    data.append(entry)
    with open(FAILED_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.warning(f"Зафиксирована неудача для {source_file} / {parent_id}")


def validate_and_fix_enriched_objects(objects: List[Dict]) -> List[Dict]:
    """Добавляет отсутствующие поля в обогащённые объекты."""
    required_fields = [
        "chunk_content", "breadcrumbs", "chunk_summary",
        "hypothetical_questions", "keywords", "entities"
    ]
    validated = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        fixed = {}
        for field in required_fields:
            if field in obj and obj[field] is not None:
                fixed[field] = obj[field]
            else:
                if field == "hypothetical_questions":
                    fixed[field] = []
                elif field == "keywords":
                    fixed[field] = []
                elif field == "entities":
                    fixed[field] = []
                elif field == "breadcrumbs":
                    fixed[field] = ""
                else:
                    fixed[field] = ""
        validated.append(fixed)
    return validated


# ================= ОСНОВНАЯ ФУНКЦИЯ ОБОГАЩЕНИЯ =================
async def enrich_chunk(
    chunk_text: str,
    source_file: str,
    category: str
) -> Optional[List[Dict]]:
    parent_id = generate_parent_chunk_id(source_file, chunk_text)

    if len(chunk_text) > 20000:
        chunk_text = chunk_text[:20000]

    few_shot_block = ""
    if few_shot_examples:
        examples_str = "\n".join(f"- {q}" for q in few_shot_examples)
        few_shot_block = f"""
    ПРИМЕРЫ РЕАЛЬНЫХ ВОПРОСОВ ПОЛЬЗОВАТЕЛЕЙ (используй их как образец стиля для hypothetical_questions):
    {examples_str}
    """

    prompt = f"""Ты эксперт по обработке и структурированию документов в сфере электроэнергетики и технологического присоединения.

Категория документа: {category}
Имя файла: {source_file}

Исходный текст чанка (может содержать несколько логических блоков, разделённых маркдауном):

{chunk_text}

---

ТВОЯ ЗАДАЧА:
1. Разделить текст на **атомарные, самодостаточные фрагменты** (по заголовкам, спискам, смысловым абзацам). Таблицы можешь делить по строке by rows и логически связанные списки. Заявление не нужно делить на атомарные элементы, его вообще нельзя делить !
2. Для каждого фрагмента исправь очевидные ошибки Markdown (если есть).
3. Для каждого фрагмента создай объект JSON со следующими полями:
   - `chunk_content` (строка): полный текст фрагмента с исправленным Markdown.
   - `breadcrumbs` (строка): путь заголовков от корня документа до этого фрагмента, разделённый " > " (например "Глава 1 > Статья 3"). Если заголовков нет, оставь пустую строку.
   - `chunk_summary` (строка): краткое описание сути фрагмента (2-4 предложения на русском).
   - `hypothetical_questions` (массив строк): 4-5 вопросов, которые мог бы задать пользователь, чтобы найти этот фрагмент (на русском).
   - `keywords` (массив строк): 5-10 ключевых слов или фраз (на русском).
   - `entities` (массив строк): именованные сущности (организации, законы, даты, термины) — 3-8 штук.


ВАЖНО:
- Все текстовые поля должны быть **только на русском языке**.
- Верни **строго валидный JSON-массив** (без пояснений, без обёрток ```json).
- Массив может содержать от 1 до N объектов в зависимости от размера исходного текста.
- Каждый объект должен быть самодостаточным.

Пример корректного ответа (но ты можешь создать свою структуру, главное — соблюсти поля):
[
  {{
    "chunk_content": "# Глава 1. Общие положения\\n\\n## Статья 1. Предмет регулирования\\n1. Настоящий Федеральный закон устанавливает правовые основы...",
    "breadcrumbs": "Глава 1. Общие положения > Статья 1. Предмет регулирования",
    "chunk_summary": "Статья определяет предмет регулирования Федерального закона № 35-ФЗ, а именно правовые основы экономических отношений в сфере электроэнергетики.",
    "hypothetical_questions": [
      "Что регулирует Федеральный закон № 35-ФЗ?",
      "Какие отношения устанавливает данный закон?",
      "Кто является субъектами электроэнергетики?",
      "Какие полномочия определяет закон для органов власти?"
    ],
    "keywords": [
      "предмет регулирования",
      "электроэнергетика",
      "правовые основы",
      "экономические отношения",
      "субъекты электроэнергетики"
    ],
    "entities": [
      "Федеральный закон № 35-ФЗ",
      "электроэнергетика",
      "Правительство Российской Федерации"
    ]
  }}
]

Твой ответ (только JSON):
"""

    messages = [
        {"role": "system", "content": "Ты помощник, который возвращает только JSON без дополнительных пояснений."},
        {"role": "user", "content": prompt}
    ]

    last_raw = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

            async with semaphore:
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS
                )

            raw = response.choices[0].message.content or ""
            last_raw = raw
            logger.debug(f"Получен ответ, длина {len(raw)}")
            save_raw_response(raw, source_file, parent_id, attempt)

            cleaned = clean_json_string(raw)
            if not cleaned:
                logger.debug("Пустой ответ после очистки")
                continue

            data = json.loads(cleaned)
            if isinstance(data, dict):
                data = [data]
            if not isinstance(data, list):
                logger.debug("Ответ не является массивом")
                continue

            validated_data = validate_and_fix_enriched_objects(data)

            enriched = []
            for idx, obj in enumerate(validated_data, start=1):
                obj["chunk_id"] = f"{parent_id}_p{idx}"
                obj["source_file"] = source_file
                obj["category"] = category
                enriched.append(obj)
            return enriched

        except json.JSONDecodeError as e:
            logger.warning(f"JSON ошибка (попытка {attempt+1}): {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка API (попытка {attempt+1}): {e}")
            continue

    if last_raw:
        recovered = repair_json(last_raw)
        if recovered:
            logger.info(f"🔧 Восстановлено через repair для {source_file} / {parent_id}")
            validated_recovered = validate_and_fix_enriched_objects(recovered)
            enriched = []
            for idx, obj in enumerate(validated_recovered, start=1):
                obj["chunk_id"] = f"{parent_id}_p{idx}"
                obj["source_file"] = source_file
                obj["category"] = category
                enriched.append(obj)
            return enriched
        else:
            log_failure(source_file, parent_id, last_raw)
    else:
        log_failure(source_file, parent_id, "No response")

    return None


# ================= ОБРАБОТКА ФАЙЛА =================
async def process_file(file_path: Path):
    file_name = file_path.name
    base_name = file_path.stem  # имя без расширения
    # Если файл в списке обработанных – пропускаем
    if file_name in PROCESSED_FILES:
        logger.info(f"Файл {file_name} находится в списке обработанных, пропускаем")
        return
    # Папка для сохранения результатов (с подпапкой категории)
    output_subdir = OUTPUT_DIR / CATEGORY
    output_subdir.mkdir(parents=True, exist_ok=True)

    # Читаем исходный файл
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = content.split(CHUNK_SEPARATOR)
    chunks = [c.strip() for c in chunks if c.strip()]

    if not chunks:
        logger.warning(f"Файл {file_name} не содержит чанков")
        return

    # Собираем уже обработанные parent_id по наличию файлов
    processed_parent_ids = set()
    # Ищем все файлы вида: baseName_*_p*.json
    pattern = re.compile(rf"^{re.escape(base_name)}_(.*?)_p\d+\.json$")
    for existing_file in output_subdir.glob(f"{base_name}_*_p*.json"):
        match = pattern.match(existing_file.name)
        if match:
            parent_id = match.group(1)
            processed_parent_ids.add(parent_id)

    logger.info(f"Файл {file_name}: всего чанков {len(chunks)}, уже обработано {len(processed_parent_ids)}")

    # Определяем, какие чанки ещё не обработаны
    chunks_to_process = []
    for chunk in chunks:
        parent_id = generate_parent_chunk_id(file_name, chunk)
        if parent_id not in processed_parent_ids:
            chunks_to_process.append((parent_id, chunk))

    if not chunks_to_process:
        logger.info(f"Все чанки в {file_name} уже обработаны")
        return

    # Обрабатываем только новые чанки
    for parent_id, chunk in tqdm(chunks_to_process, desc=file_name):
        enriched = await enrich_chunk(chunk, file_name, CATEGORY)
        if enriched:
            for idx, obj in enumerate(enriched, start=1):
                chunk_filename = f"{base_name}_{parent_id}_p{idx}.json"
                chunk_path = output_subdir / chunk_filename
                with open(chunk_path, "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
                logger.debug(f"Сохранён {chunk_path}")
        else:
            logger.warning(f"Не удалось обработать чанк {parent_id} – он будет повторно запрошен при следующем запуске")


# ================= ГЛАВНАЯ ФУНКЦИЯ =================
async def main():
    category_path = CHUNKS_DIR / CATEGORY
    if not category_path.exists():
        logger.error(f"Папка {category_path} не существует")
        return

    files = list(category_path.glob("*.md"))
    if not files:
        logger.warning(f"В папке {category_path} нет .md файлов")
        return

    logger.info(f"Найдено файлов: {len(files)}")
    for file_path in files:
        await process_file(file_path)

    logger.info("🏁 Все файлы обработаны")


if __name__ == "__main__":
    logger.info("="*50)
    logger.info("ЗАПУСК ОБРАБОТЧИКА")
    logger.info(f"Категория: {CATEGORY}")
    logger.info(f"Папка с исходниками: {CHUNKS_DIR / CATEGORY}")
    logger.info(f"Папка для результатов: {OUTPUT_DIR / CATEGORY}")
    logger.info("="*50)
    asyncio.run(main())