#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM Chunking Pipeline v6 — Bashkirenergo AI Assistant

Пайплайн:
1. pre_split_for_llm.py → _partN.md файлы (≤50k токенов)
2. Этот скрипт: ВЕСЬ файл отправляется LLM → LLM САМ делит на атомарные чанки
3. LLM определяет ВСЕ метаданные из контента и имени файла (НЕТ маппинга!)
4. Чанки > 8000 символов → post-validation: повторный LLM-запрос на дробление
5. LLM возвращает массив JSON чанков → каждый сохраняется отдельно

Принципы:
- LLM сам определяет границы чанков и ВСЕ метаданные (category, collection_name,
  document_type, power_range, client_type — ИЗ КОНТЕКСТА)
- Динамический промпт: количество чанков = len/3500 ±3
- chunk_content сохраняется СЛОВО В СЛОВО, без сокращений
- keywords — объединённое поле (ключевые фразы + именованные сущности)
- hypothetical_questions: 3-5 штук

Формат выхода:
  chunk_id, source_file, chunk_content, breadcrumbs, chunk_summary,
  hypothetical_questions, keywords, category, collection_name,
  document_type, power_range, client_type
"""

import os
import re
import json
import asyncio
import hashlib
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from openai import AsyncOpenAI
from tqdm import tqdm

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ================= НАСТРОЙКИ =================

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = SCRIPT_DIR.parent.parent / "new_data" / "source"

MARKDOWN_SPLIT_DIR = (BASE_DIR / "markdown_data_split").resolve()
HTML_SPLIT_DIR = (BASE_DIR / "html_pages_split").resolve()

OUTPUT_BASE = SCRIPT_DIR / "enriched_chunks"
OUTPUT_NORMATIVE = OUTPUT_BASE / "normative"
OUTPUT_OPERATIONAL = OUTPUT_BASE / "operational"

LOGS_DIR = SCRIPT_DIR / "logs"
RAW_DIR = SCRIPT_DIR / "raw_responses_v6"

for d in [OUTPUT_NORMATIVE, OUTPUT_OPERATIONAL, LOGS_DIR, RAW_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API
API_KEY = "sk-5ArynRNUi11lFMyvtj5NBv4bFPS0xBs0"
BASE_URL = "https://routerai.ru/api/v1"


def get_chunking_model() -> str:
    env_path = SCRIPT_DIR.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("CHUNKING_LLM_MODEL="):
                    return line.split("=", 1)[1].strip()
    return "qwen/qwen3.5-flash-02-23"


MODEL_NAME = get_chunking_model()
TIMEOUT = 600
MAX_OUTPUT_TOKENS = 80000
TEMPERATURE = 0.15
MAX_RETRIES = 5
BASE_DELAY = 2
MAX_CONCURRENT_REQUESTS = 8

# Chunk size limits
MAX_CHUNK_CHARS = 15000
TARGET_CHARS_PER_CHUNK = 3500

# ================= ЛОГГЕР =================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "processing_v6.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
FAILED_LOG = LOGS_DIR / "failed_chunks_v6.json"

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT)
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# ================= УТИЛИТЫ =================


def clean_source_file(filename: str) -> str:
    """Убирает _partN суффикс и .md расширение. Возвращает чистое название документа."""
    stem = Path(filename).stem
    stem = re.sub(r'_part\d+$', '', stem)
    stem = re.sub(r'_part\d+$', '', stem)
    return stem


def generate_parent_chunk_id(source_file: str, file_content: str) -> str:
    """MD5 от имени файла + первых 200 символов."""
    hash_input = f"{source_file}:{file_content[:200]}".encode()
    return hashlib.md5(hash_input).hexdigest()[:12]


def clean_json_string(text: str) -> str:
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


def repair_json(raw: str) -> Optional[List]:
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
        cleaned = re.sub(r'\\(?!["\\/bfnrtu]|u[0-9a-fA-F]{4})', r'\\\\', cleaned)
        data = json.loads(cleaned)
        if isinstance(data, list) and len(data) > 0:
            return data
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, list) and len(val) > 0:
                    return val
            return [data]
    except Exception as e:
        logger.debug(f"repair_json не удался: {e}")
    return None


def save_raw_response(content: str, source_file: str, parent_id: str, attempt: int):
    filename = f"{source_file}_{parent_id}_attempt{attempt}.txt"
    path = RAW_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def log_failure(source_file: str, parent_id: str, raw_response: str):
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


# ================= ВАЛИДАЦИЯ =================

REQUIRED_FIELDS = [
    "chunk_content", "breadcrumbs", "chunk_summary",
    "hypothetical_questions", "keywords",
    "category", "collection_name", "document_type",
    "power_range", "client_type"
]

VALID_CATEGORIES = {"ТПП", "ДУ", "ЛК"}
VALID_COLLECTIONS = {"normative_documents", "operational_content"}
VALID_DOC_TYPES = {"regulation", "faq", "stage_description", "infomaterial", "instruction"}
VALID_POWER_RANGES = {"<15kW", "15-150kW", "150-670kW", ">670kW", "any"}
VALID_CLIENT_TYPES = {"ФЛ", "ИП", "ЮЛ", "any"}


def validate_chunk(obj: Dict) -> Optional[Dict]:
    """Валидирует и фиксирует один чанк."""
    if not isinstance(obj, dict):
        return None

    fixed = {}

    # chunk_content — обязательное
    content = obj.get("chunk_content", "").strip()
    if not content:
        return None
    fixed["chunk_content"] = content

    # breadcrumbs — обязательно
    bc = obj.get("breadcrumbs", "").strip()
    fixed["breadcrumbs"] = bc if bc else "Документ"

    # chunk_summary — обязательно
    summary = obj.get("chunk_summary", "").strip()
    fixed["chunk_summary"] = summary if summary else "Описание отсутствует"

    # hypothetical_questions — 3-5 штук, берём первые 5
    hq = obj.get("hypothetical_questions", [])
    if not isinstance(hq, list):
        hq = []
    hq = [q.strip() for q in hq if isinstance(q, str) and q.strip()]
    fixed["hypothetical_questions"] = hq[:5]

    # keywords — объединённое поле (ключевые фразы + именованные сущности)
    kw = obj.get("keywords", [])
    if not isinstance(kw, list):
        kw = []
    kw = [k.strip() for k in kw if isinstance(k, str) and k.strip()]
    fixed["keywords"] = kw

    # category
    cat = obj.get("category", "").strip()
    fixed["category"] = cat if cat in VALID_CATEGORIES else "ТПП"

    # collection_name
    col = obj.get("collection_name", "").strip()
    fixed["collection_name"] = col if col in VALID_COLLECTIONS else "operational_content"

    # document_type
    dt = obj.get("document_type", "").strip()
    fixed["document_type"] = dt if dt in VALID_DOC_TYPES else "infomaterial"

    # power_range
    pr = obj.get("power_range", "").strip()
    fixed["power_range"] = pr if pr in VALID_POWER_RANGES else "any"

    # client_type
    ct = obj.get("client_type", "").strip()
    fixed["client_type"] = ct if ct in VALID_CLIENT_TYPES else "any"

    return fixed


# ================= ПРОМПТ =================

def build_prompt(file_content: str, source_file: str) -> str:
    content_len = len(file_content)
    target = max(1, content_len // TARGET_CHARS_PER_CHUNK)
    chunk_min = max(1, target - 3)
    chunk_max = target + 3

    return f"""Ты эксперт по обработке документов в сфере электроэнергетики и технологического присоединения (ТП) к электросетям компании Башкирэнерго.

## Файл
- Имя: {source_file}
- Размер: {content_len} символов
- Целевое количество чанков: {chunk_min}-{chunk_max} (примерно по {TARGET_CHARS_PER_CHUNK} символов на чанк)

## Исходный текст документа

{file_content}

## Задача

Раздели этот документ на {chunk_min}-{chunk_max} атомарных смысловых чанков. Каждый чанк — самостоятельный смысловой блок (статья, пункт, раздел, ответ на вопрос, шаг инструкции).

### Правила разделения:
1. chunk_content сохраняется СЛОВО В СЛОВО — НЕ сокращай, НЕ обрезай, НЕ пересказывай
2. Каждый чанк ~2000-5000 символов. Не делай чанки меньше 1000 или больше 8000 символов
3. Объединяй мелкие пункты одной темы в один чанк
4. НЕ разрывай связанные списки, таблицы, формы заявок
5. Сохраняй Markdown-форматирование в chunk_content

### Поля каждого JSON-объекта:

1. `chunk_content` (строка) — полный текст чанка с Markdown. СЛОВО В СЛОВО из оригинала.

2. `breadcrumbs` (строка) — путь заголовков от корня документа, например: "Глава 2 > Статья 15 > Пункт 3"

3. `chunk_summary` (строка) — краткое описание сути чанка (2-4 предложения на русском)

4. `hypothetical_questions` (массив строк, от 3 до 5 штук) — конкретные поисковые вопросы клиента Башкирэнерго.
   - Формулируй как РЕАЛЬНЫЙ КЛИЕНТ, а не как аналитик
   - НУЖНЫ конкретные: "Какой срок подключения до 15 кВт?", "Сколько стоит ТП для физлиц?"
   - Для нормативных документов: ссылайся на конкретные статьи и пункты
   - Для операционных: вопросы про процедуры, сроки, стоимость, порядок действий

5. `keywords` (массив строк, 5-10 штук) — ключевые фразы ДЛЯ ПОИСКА. Содержит как термины, так и именованные сущности:
   - Термины: "технологическое присоединение", "подача заявки"
   - Организации: "ООО «Башкирэнерго»"
   - Номера законов: "ФЗ №35-ФЗ", "Постановление №861"
   - Числа и даты: "15 кВт", "2024 год"
   - Ключевые фразы: "осмотр электроустановки", "акт об осуществлении ТП"
   ВАЖНО: это ЕДИНСТВЕННОЕ поле для поиска — включи сюда всё, что нужно для поиска этого чанка

6. `category` (строка) — категория домена. Определи из контекста документа:
   - "ТПП" — технологическое присоединение (основные правила, процедуры, нормы)
   - "ДУ" — дополнительные услуги (сопутствующие платные услуги)
   - "ЛК" — личный кабинет (работа с личным кабинетом, инструкции)

7. `collection_name` (строка) — коллекция Qdrant. Определи по типу документа:
   - "normative_documents" — если это закон, постановление, приказ, нормативный акт
   - "operational_content" — если это FAQ, инструкция, памятка, описание этапа, паспорт услуги

8. `document_type` (строка) — тип документа. Определи по содержанию:
   - "regulation" — нормативный акт (закон, постановление, правила)
   - "faq" — часто задаваемые вопросы
   - "stage_description" — описание этапа процесса
   - "infomaterial" — информационный материал, памятка
   - "instruction" — пошаговая инструкция, паспорт услуги

9. `power_range` (строка) — диапазон мощности. Определи по контексту:
   - "<15kW" — до 15 кВт
   - "15-150kW" — от 15 до 150 кВт
   - "150-670kW" — от 150 до 670 кВт
   - ">670kW" — свыше 670 кВт
   - "any" — применимо ко всем диапазонам

10. `client_type` (строка) — тип клиента. Определи по контексту:
    - "ФЛ" — физические лица
    - "ИП" — индивидуальные предприниматели
    - "ЮЛ" — юридические лица
    - "any" — применимо ко всем

### Формат ответа

Верни строго валидный JSON-массив объектов. Без пояснений, без обёрток, без markdown.

Пример:
[
  {{
    "chunk_content": "Статья 26. Сетевая организация обязана...",
    "breadcrumbs": "Глава 4 > Статья 26",
    "chunk_summary": "Статья 26 устанавливает обязанность сетевой организации по технологическому присоединению.",
    "hypothetical_questions": [
      "Обязана ли сетевая организация подключить мой дом?",
      "Когда могут отказать в присоединении?"
    ],
    "keywords": ["технологическое присоединение", "обязанность сетевой организации", "статья 26", "ФЗ №35-ФЗ"],
    "category": "ТПП",
    "collection_name": "normative_documents",
    "document_type": "regulation",
    "power_range": "any",
    "client_type": "any"
  }}
]"""


# ================= POST-VALIDATION =================

def build_split_prompt(chunk: Dict, source_file: str) -> str:
    """Промпт для дробления oversized чанка."""
    content = chunk["chunk_content"]
    content_len = len(content)
    target = max(2, content_len // TARGET_CHARS_PER_CHUNK)
    chunk_min = max(2, target - 2)
    chunk_max = target + 2

    hints = (
        f"Родительские метаданные (для справки):\n"
        f"- category: {chunk.get('category', 'ТПП')}\n"
        f"- collection_name: {chunk.get('collection_name', 'operational_content')}\n"
        f"- document_type: {chunk.get('document_type', 'infomaterial')}\n"
        f"- source_file: {source_file}\n"
        f"- parent_breadcrumbs: {chunk.get('breadcrumbs', 'Документ')}\n"
    )

    return f"""Ты эксперт по обработке документов Башкирэнерго.

Этот фрагмент документа слишком большой ({content_len} символов), его нужно разделить на более мелкие части.

{hints}
## Текст фрагмента для разделения

{content}

## Задача

Раздели этот текст на {chunk_min}-{chunk_max} самодостаточных частей. Для КАЖДОЙ части верни JSON-объект с полями:
- chunk_content (строка) — текст части, слово в слово
- breadcrumbs (строка) — уточнённый путь заголовков для этой части
- chunk_summary (строка) — краткое описание (1-2 предложения)
- hypothetical_questions (массив, 3-5 штук) — поисковые вопросы для этой части
- keywords (массив, 5-10 штук) — ключевые фразы + сущности
- power_range (строка) — определи для ЭТОЙ части
- client_type (строка) — определи для ЭТОЙ части

ВАЖНО:
- Каждая часть должна быть самодостаточной и иметь смысл отдельно
- Объём каждой части: ~{TARGET_CHARS_PER_CHUNK} символов
- Поля power_range и client_type определяй ЗАНОВО для каждой части (не копируй из родительских)

Верни строго валидный JSON-массив без пояснений."""


async def split_oversized_chunk(chunk: Dict, source_file: str, parent_id: str, idx: int) -> Optional[List[Dict]]:
    """Отправляет oversized чанк на повторный LLM-запрос для дробления."""
    prompt = build_split_prompt(chunk, source_file)

    messages = [
        {"role": "system", "content": "Ты помощник, который возвращает только валидный JSON-массив без дополнительных пояснений."},
        {"role": "user", "content": prompt}
    ]

    last_raw = None
    sub_chunks = None

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
                    max_tokens=MAX_OUTPUT_TOKENS,
                    response_format={"type": "json_object"},
                )

            raw = response.choices[0].message.content or ""
            last_raw = raw

            cleaned = clean_json_string(raw)
            if not cleaned:
                continue

            data = json.loads(cleaned)
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        data = val
                        break
                else:
                    data = [data]

            if not isinstance(data, list):
                continue

            valid = []
            for item in data:
                validated = validate_chunk(item)
                if validated:
                    valid.append(validated)

            if valid:
                sub_chunks = valid
                logger.info(f"    ✅ Дробление: {len(sub_chunks)} под-чанков")
                break

        except json.JSONDecodeError as e:
            logger.debug(f"JSON ошибка в split (попытка {attempt+1}): {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка API в split (попытка {attempt+1}): {e}")
            continue

    if not sub_chunks and last_raw:
        recovered = repair_json(last_raw)
        if recovered:
            valid = []
            for item in recovered:
                validated = validate_chunk(item)
                if validated:
                    valid.append(validated)
            if valid:
                sub_chunks = valid
                logger.info(f"    🔧 Дробление через repair: {len(sub_chunks)} под-чанков")

    if not sub_chunks:
        logger.warning(f"    ❌ Не удалось раздробить chunk p{idx}")
        return None

    # Проставляем ID и наследуем общие поля
    for sub_idx, sc in enumerate(sub_chunks, 1):
        sc["chunk_id"] = f"{parent_id}_p{idx}_sub{sub_idx}"
        sc["source_file"] = source_file
        for field in ["category", "collection_name", "document_type"]:
            if field not in sc or not sc.get(field):
                sc[field] = chunk.get(field, "")

    return sub_chunks


async def post_validate_chunks(chunks: List[Dict], source_file: str, parent_id: str) -> List[Dict]:
    """Проверяет размеры чанков и дробит oversized через LLM."""
    result = []

    for idx, chunk in enumerate(chunks, 1):
        content = chunk.get("chunk_content", "")
        if len(content) > MAX_CHUNK_CHARS:
            logger.info(f"  → Chunk p{idx} слишком большой ({len(content)} символов), дроблю...")
            sub_chunks = await split_oversized_chunk(chunk, source_file, parent_id, idx)
            if sub_chunks:
                result.extend(sub_chunks)
            else:
                # Если дробление не удалось, сохраняем как есть с оригинальным ID
                chunk["chunk_id"] = f"{parent_id}_p{idx}"
                result.append(chunk)
        else:
            chunk["chunk_id"] = f"{parent_id}_p{idx}"
            result.append(chunk)

    return result


# ================= ОСНОВНАЯ ФУНКЦИЯ =================

async def process_file(file_path: Path, is_html: bool):
    del is_html  # не используется (нет маппинга для HTML)
    file_name = file_path.name
    clean_name = clean_source_file(file_name)
    base_name = Path(file_name).stem

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        logger.warning(f"⏭️ {file_name}: пустой файл, пропускаем")
        return

    parent_id = generate_parent_chunk_id(file_name, content)

    # Проверяем уже обработанные чанки (по parent_id в любой из папок)
    existing_norm = list(OUTPUT_NORMATIVE.glob(f"{base_name}_{parent_id}_p*.json"))
    existing_oper = list(OUTPUT_OPERATIONAL.glob(f"{base_name}_{parent_id}_p*.json"))
    if existing_norm or existing_oper:
        logger.info(f"📄 {file_name}: уже обработан ({len(existing_norm) + len(existing_oper)} чанков), пропускаем")
        return

    logger.info(f"📄 {file_name}: {len(content)} символов")

    prompt = build_prompt(content, file_name)

    messages = [
        {"role": "system", "content": "Ты помощник, который возвращает только валидный JSON-массив без дополнительных пояснений."},
        {"role": "user", "content": prompt}
    ]

    last_raw = None
    chunks = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.info(f"Retry {attempt+1}/{MAX_RETRIES} для {file_name}, задержка {delay}с")
                await asyncio.sleep(delay)

            async with semaphore:
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    response_format={"type": "json_object"},
                )

            raw = response.choices[0].message.content or ""
            last_raw = raw
            save_raw_response(raw, file_name, parent_id, attempt)

            cleaned = clean_json_string(raw)
            if not cleaned:
                logger.debug("Пустой ответ после очистки")
                continue

            data = json.loads(cleaned)

            # Нормализуем: всегда должен быть список
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        data = val
                        break
                else:
                    data = [data]

            if not isinstance(data, list):
                logger.debug("Ответ не является массивом")
                continue

            # Валидируем каждый чанк
            valid_chunks = []
            for item in data:
                validated = validate_chunk(item)
                if validated:
                    valid_chunks.append(validated)

            if valid_chunks:
                chunks = valid_chunks
                logger.info(f"✅ {file_name}: {len(chunks)} чанков (начально)")
                break
            else:
                logger.warning(f"Нет валидных чанков в ответе для {file_name}")

        except json.JSONDecodeError as e:
            logger.warning(f"JSON ошибка (попытка {attempt+1}): {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка API (попытка {attempt+1}): {e}")
            continue

    if not chunks and last_raw:
        recovered = repair_json(last_raw)
        if recovered and isinstance(recovered, list):
            valid_chunks = []
            for item in recovered:
                validated = validate_chunk(item)
                if validated:
                    valid_chunks.append(validated)
            if valid_chunks:
                chunks = valid_chunks
                logger.info(f"🔧 {file_name}: восстановлено через repair, {len(chunks)} чанков")

    if not chunks:
        log_failure(file_name, parent_id, last_raw or "No response")
        logger.warning(f"❌ Не удалось обработать {file_name}")
        return

    # Post-validation: дробим oversized чанки
    oversized_before = sum(1 for c in chunks if len(c.get("chunk_content", "")) > MAX_CHUNK_CHARS)
    if oversized_before:
        logger.info(f"  🔍 Post-validation: {oversized_before}/{len(chunks)} чанков >{MAX_CHUNK_CHARS}")
        chunks = await post_validate_chunks(chunks, clean_name, parent_id)
        oversized_after = sum(1 for c in chunks if len(c.get("chunk_content", "")) > MAX_CHUNK_CHARS)
        logger.info(f"  ✅ После: {len(chunks)} чанков (>{MAX_CHUNK_CHARS}: {oversized_after})")
    else:
        # Небольшие чанки — проставляем ID без post-validation
        for idx, chunk in enumerate(chunks, 1):
            chunk["chunk_id"] = f"{parent_id}_p{idx}"

    # Сохраняем чанки (routing по collection_name из LLM)
    for chunk in chunks:
        chunk["source_file"] = clean_name
        collection = chunk.get("collection_name", "operational_content")
        output_dir = OUTPUT_NORMATIVE if collection == "normative_documents" else OUTPUT_OPERATIONAL
        output_dir.mkdir(parents=True, exist_ok=True)

        chunk_filename = f"{base_name}_{chunk['chunk_id']}.json"
        chunk_path = output_dir / chunk_filename
        with open(chunk_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 {file_name}: сохранено {len(chunks)} чанков")


# ================= ГЛАВНАЯ ФУНКЦИЯ =================

async def main():
    logger.info("=" * 60)
    logger.info("ЗАПУСК LLM CHUNKING v6")
    logger.info(f"Модель: {MODEL_NAME}")
    logger.info(f"Max concurrent: {MAX_CONCURRENT_REQUESTS}")
    logger.info(f"Max output tokens: {MAX_OUTPUT_TOKENS}")
    logger.info(f"Target chars/chunk: {TARGET_CHARS_PER_CHUNK}")
    logger.info(f"Max chars (post-valid): {MAX_CHUNK_CHARS}")
    logger.info(f"markdown_data_split: {MARKDOWN_SPLIT_DIR}")
    logger.info(f"html_pages_split: {HTML_SPLIT_DIR}")
    logger.info(f"Выход normative: {OUTPUT_NORMATIVE}")
    logger.info(f"Выход operational: {OUTPUT_OPERATIONAL}")
    logger.info("Маппинг: ОТКЛЮЧЁН — LLM определяет всё сама")
    logger.info("=" * 60)

    tasks = []

    if MARKDOWN_SPLIT_DIR.exists():
        md_files = sorted(MARKDOWN_SPLIT_DIR.glob("*.md"))
        logger.info(f"\n📂 markdown_data_split: {len(md_files)} файлов")
        for fp in md_files:
            tasks.append(process_file(fp, is_html=False))
    else:
        logger.warning(f"Папка {MARKDOWN_SPLIT_DIR} не найдена")

    if HTML_SPLIT_DIR.exists():
        html_files = sorted(HTML_SPLIT_DIR.glob("*.md"))
        logger.info(f"\n📂 html_pages_split: {len(html_files)} файлов")
        for fp in html_files:
            tasks.append(process_file(fp, is_html=True))
    else:
        logger.warning(f"Папка {HTML_SPLIT_DIR} не найдена")

    if not tasks:
        logger.warning("⚠️ Нет файлов для обработки!")
        return

    logger.info(f"\n🚀 Запуск {len(tasks)} файлов (семафор={MAX_CONCURRENT_REQUESTS})")
    await asyncio.gather(*tasks)

    # Статистика
    norm_count = len(list(OUTPUT_NORMATIVE.glob("*.json")))
    oper_count = len(list(OUTPUT_OPERATIONAL.glob("*.json")))
    total_chunks = norm_count + oper_count

    logger.info(f"\n🏁 Все файлы обработаны")
    logger.info(f"📊 Normative: {norm_count} чанков")
    logger.info(f"📊 Operational: {oper_count} чанков")
    logger.info(f"📊 Всего: {total_chunks} чанков")


if __name__ == "__main__":
    asyncio.run(main())
