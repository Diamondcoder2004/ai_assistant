#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Асинхронный обогатитель чанков для new_data.
Использует deepseek-v4-flash с JSON output mode.
Поддерживает докачку, retry, маппинг категорий и source_origin.
"""

import os
import re
import json
import asyncio
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from openai import AsyncOpenAI
from tqdm import tqdm

# ================= МАППИНГ ФАЙЛОВ =================

# Нормативные документы (из markdown_data, совпадают с PDF из normative/)
NORMATIVE_FILES = {
    "1. ФЗ 35 (28.04.2025)": {"category": "Общая", "source_origin": "normative"},
    "2. 861 (28.04.2025)": {"category": "ТПП", "source_origin": "normative"},
    "1178-cenoobrazovanie": {"category": "ТПП", "source_origin": "normative"},
    "186-minenergo-standarty-kachestva": {"category": "Общая", "source_origin": "normative"},
    "4. 490_22 Методические указания": {"category": "ТПП", "source_origin": "normative"},
    "9. 442 О ФУНКЦИОНИРОВАНИИ РОЗНИЧНЫХ РЫНКОВ": {"category": "Общая", "source_origin": "normative"},
    "gkt-rb-306-plata-2026": {"category": "ТПП", "source_origin": "normative"},
}

# Операционные документы из markdown_data
OPERATIONAL_MD_FILES = {
    "10. Инструкция по работе в ЛК (для заявителя) (от января 2024)": {"category": "ЛК", "source_origin": "operational"},
    "7. Инструкция по самостоятельному подключению": {"category": "ТПП", "source_origin": "operational"},
    "faq-kt-tpp-2026": {"category": "ТПП", "source_origin": "operational"},
    "pamyatka-do-670kvt": {"category": "ТПП", "source_origin": "operational"},
    "pamyatka-svyshe-670kvt": {"category": "ТПП", "source_origin": "operational"},
    "passport-individualnyy-proekt": {"category": "ТПП", "source_origin": "operational"},
    "passport-pereraspredelenie": {"category": "ТПП", "source_origin": "operational"},
    "passport-tp-15-150kvt": {"category": "ТПП", "source_origin": "operational"},
    "passport-tp-150-670kvt": {"category": "ТПП", "source_origin": "operational"},
    "passport-tp-do-15kvt": {"category": "ТПП", "source_origin": "operational"},
    "passport-tp-svyshe-670kvt": {"category": "ТПП", "source_origin": "operational"},
    "passport-vosstanovlenie": {"category": "ТПП", "source_origin": "operational"},
    "passport-vremennoe-tp": {"category": "ТПП", "source_origin": "operational"},
    "passport-vyvod-iz-ekspluatatsii": {"category": "ТПП", "source_origin": "operational"},
}

# ================= НАСТРОЙКИ =================

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = SCRIPT_DIR / ".." / ".." / "new_data" / "source"

# Входные папки (после pre_split_for_llm.py)
MARKDOWN_SPLIT_DIR = (BASE_DIR / "markdown_data_split").resolve()
HTML_SPLIT_DIR = (BASE_DIR / "html_pages_split").resolve()

# Метаданные html_pages
METADATA_PATH = (BASE_DIR / "operational" / "metadata.json").resolve()

# Выходные папки
OUTPUT_BASE = SCRIPT_DIR / "enriched_chunks"
OUTPUT_NORMATIVE = OUTPUT_BASE / "normative"
OUTPUT_OPERATIONAL = OUTPUT_BASE / "operational"

# Логи
LOGS_DIR = SCRIPT_DIR / "logs"
RAW_DIR = SCRIPT_DIR / "raw_responses_v3"

# Создаём папки
for d in [OUTPUT_NORMATIVE, OUTPUT_OPERATIONAL, LOGS_DIR, RAW_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API настройки
API_KEY = "sk-5ArynRNUi11lFMyvtj5NBv4bFPS0xBs0"
BASE_URL = "https://routerai.ru/api/v1"
MODEL_NAME = "deepseek/deepseek-v4-flash"
TIMEOUT = 600
MAX_TOKENS = 80_000
TEMPERATURE = 0.15
MAX_RETRIES = 5
BASE_DELAY = 2
MAX_CONCURRENT_REQUESTS = 3

CHUNK_SEPARATOR = "\n\n---CHUNK---\n\n"

# ================= НАСТРОЙКА ЛОГГЕРА =================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "processing_v3.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
FAILED_LOG = LOGS_DIR / "failed_chunks_v3.json"

# ================= ИНИЦИАЛИЗАЦИЯ КЛИЕНТА =================

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT)
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


# ================= ЗАГРУЗКА МЕТАДАННЫХ HTML =================

def load_html_metadata() -> Dict[str, Dict]:
    """Загружает категории html_pages из metadata.json."""
    if not METADATA_PATH.exists():
        logger.warning(f"metadata.json не найден: {METADATA_PATH}")
        return {}
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    result = {}
    for item in meta.get("html_pages", []):
        fname = item["file"]
        # Маппинг category: ДУ → ДУ, ТПП → ТПП
        cat = item.get("category", "ТПП")
        result[Path(fname).stem] = {
            "category": cat,
            "source_origin": "operational",
            "document_source": "html_page",
            "description": item.get("description", ""),
        }
    return result


HTML_METADATA = load_html_metadata()


# ================= ОПРЕДЕЛЕНИЕ МЕТАДАННЫХ ФАЙЛА =================

def get_file_metadata(filename: str, is_html: bool) -> Dict:
    """Определяет category, source_origin, document_source для файла."""
    stem = Path(filename).stem
    # Убираем _partN суффикс для поиска в маппинге
    base_stem = re.sub(r'_part\d+$', '', stem)

    if is_html:
        meta = HTML_METADATA.get(base_stem, {})
        return {
            "category": meta.get("category", "ТПП"),
            "source_origin": "operational",
            "document_source": "html_page",
        }

    # markdown_data — проверяем normative или operational
    if base_stem in NORMATIVE_FILES:
        info = NORMATIVE_FILES[base_stem]
        return {
            "category": info["category"],
            "source_origin": "normative",
            "document_source": "pdf",
        }

    if base_stem in OPERATIONAL_MD_FILES:
        info = OPERATIONAL_MD_FILES[base_stem]
        return {
            "category": info["category"],
            "source_origin": "operational",
            "document_source": "pdf",
        }

    # Фоллбэк
    logger.warning(f"Файл {filename} не найден в маппинге, используем ТПП/operational/pdf")
    return {"category": "ТПП", "source_origin": "operational", "document_source": "pdf"}


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
    """Записывает информацию о провалившемся чанке."""
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


REQUIRED_FIELDS = [
    "chunk_content", "breadcrumbs", "chunk_summary",
    "hypothetical_questions", "keywords", "entities"
]

def validate_and_fix_enriched_objects(objects: List[Dict]) -> List[Dict]:
    """Добавляет отсутствующие поля в обогащённые объекты."""
    validated = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        fixed = {}
        for field in REQUIRED_FIELDS:
            if field in obj and obj[field] is not None:
                fixed[field] = obj[field]
            elif field in ("hypothetical_questions", "keywords", "entities"):
                fixed[field] = []
            elif field == "breadcrumbs":
                fixed[field] = ""
            else:
                fixed[field] = ""
        validated.append(fixed)
    return validated


# ================= ПРОМПТ =================

def build_prompt(chunk_text: str, source_file: str, meta: Dict) -> str:
    category = meta["category"]
    source_origin = meta["source_origin"]
    document_source = meta["document_source"]

    origin_desc = "нормативный документ (закон, постановление, приказ)" if source_origin == "normative" else "операционный документ (инструкция, памятка, страница сайта)"
    source_desc = "PDF-документ (нормативно-правовой акт)" if document_source == "pdf" else "HTML-страница сайта Башкирэнерго"

    return f"""Ты эксперт по обработке документов в сфере электроэнергетики и технологического присоединения (ТП) к электросетям компании Башкирэнерго.

## Контекст документа
- Категория: {category}
- Тип источника: {source_desc}
- Классификация: {origin_desc}
- Файл: {source_file}

## Исходный текст

{chunk_text}

## Задача

Раздели текст на атомарные, самодостаточные фрагменты и для каждого создай JSON-объект.

### Правила деления:
- По заголовкам, статьям, пунктам, логическим блокам
- Каждый фрагмент должен быть понятен без остального текста
- Заявления и формы документов НЕ делить

### Размер фрагментов:
- Целевой размер `chunk_content`: **500–2000 символов** (примерно 3-15 предложений)
- Минимум: 300 символов — не создавай слишком мелкие фрагменты из 1-2 предложений
- Максимум: 3000 символов — если блок больше, дели его на подпункты
- Одна статья закона, один пункт правил, один FAQ-вопрос = один фрагмент

### Таблицы:
- Таблицы ≤20 строк: НЕ разделяй, включи целиком в один фрагмент
- Таблицы >20 строк: дели по логическим группам (по категории, по диапазону мощности и т.д.)
- Всегда сохраняй заголовок таблицы (первую строку с названиями колонок) в каждом фрагменте
- Если таблица является частью пункта/статьи — включи контекст (текст до/после таблицы)

### Изображения:
- Удаляй ссылки на изображения вида ![alt](url) — они бесполезны без файлов
- Сохраняй обычные ссылки [текст](url)

### Поля JSON-объекта:

1. `chunk_content` (строка) — полный текст фрагмента с исправленным Markdown (500-2000 символов)
2. `breadcrumbs` (строка) — путь заголовков: "Глава X > Статья Y > Пункт Z". Если нет — пустая строка.
3. `chunk_summary` (строка) — краткое описание сути (2-4 предложения на русском)
4. `hypothetical_questions` (массив строк) — 4-6 вопросов на русском

   КРИТИЧЕСКИ ВАЖНО для вопросов:
   - Формулируй как РЕАЛЬНЫЙ КЛИЕНТ Башкирэнерго, который ищет информацию
   - ЗАПРЕЩЕНЫ абстрактные вопросы: "Что описано в данном разделе?", "О чём этот фрагмент?", "Что написано здесь?"
   - НУЖНЫ конкретные поисковые вопросы:
     * "Какой срок подключения к электросетям до 15 кВт?"
     * "Сколько стоит технологическое присоединение для физических лиц?"
     * "Какие документы нужны для подачи заявки на ТП?"
     * "Что говорит пункт 17 Правил 861 о плате за присоединение?"
   - Для нормативных документов: ссылайся на конкретные статьи и пункты
   - Для операционных: вопросы про процедуры, сроки, стоимость, порядок действий

5. `keywords` (массив строк) — 5-10 конкретных ключевых фраз для поиска (термины, процедуры, числа)
6. `entities` (массив строк) — 3-8 именованных сущностей (законы с номерами, организации, даты, суммы, мощности в кВт)

### Формат ответа

Верни строго валидный JSON-массив объектов. Без пояснений, без обёрток, без markdown.

Пример:
[
  {{
    "chunk_content": "## Статья 26. Регулирование доступа к электрическим сетям...",
    "breadcrumbs": "Глава 4 > Статья 26",
    "chunk_summary": "Статья устанавливает обязанность сетевой организации осуществить технологическое присоединение...",
    "hypothetical_questions": [
      "Обязана ли сетевая организация подключить мой дом к электросетям?",
      "Что говорит статья 26 ФЗ-35 о технологическом присоединении?",
      "Может ли сетевая организация отказать в технологическом присоединении?",
      "Какие основания для обязательного присоединения к электросетям?"
    ],
    "keywords": ["технологическое присоединение", "сетевая организация", "доступ к электросетям", "обязанность присоединения", "энергопринимающие устройства"],
    "entities": ["Федеральный закон № 35-ФЗ", "статья 26", "сетевая организация"]
  }}
]"""


# ================= ОСНОВНАЯ ФУНКЦИЯ ОБОГАЩЕНИЯ =================

async def enrich_chunk(
    chunk_text: str,
    source_file: str,
    meta: Dict,
) -> Optional[List[Dict]]:
    parent_id = generate_parent_chunk_id(source_file, chunk_text)

    # Safety truncation: keep within model context window (~128k tokens)
    # pre_split_for_llm.py already limits input to 100k tokens, but defend in depth
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        chunk_tokens = enc.encode(chunk_text)
        if len(chunk_tokens) > 100_000:
            chunk_text = enc.decode(chunk_tokens[:100_000])
            logger.warning(f"Чанк обрезан до 100k токенов для {source_file}/{parent_id}")
    except ImportError:
        # Fallback: no tiktoken available, rely on pre_split_for_llm.py's sizing
        pass

    prompt = build_prompt(chunk_text, source_file, meta)

    messages = [
        {"role": "system", "content": "Ты помощник, который возвращает только валидный JSON без дополнительных пояснений."},
        {"role": "user", "content": prompt}
    ]

    last_raw = None

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.info(f"Retry {attempt+1}/{MAX_RETRIES} для {source_file}/{parent_id}, задержка {delay}с")
                await asyncio.sleep(delay)

            async with semaphore:
                response = await client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    response_format={"type": "json_object"},
                )

            raw = response.choices[0].message.content or ""
            last_raw = raw
            save_raw_response(raw, source_file, parent_id, attempt)

            cleaned = clean_json_string(raw)
            if not cleaned:
                logger.debug("Пустой ответ после очистки")
                continue

            data = json.loads(cleaned)

            # JSON output mode может вернуть {"chunks": [...]} вместо [...]
            if isinstance(data, dict):
                # Ищем массив в значениях
                for key, val in data.items():
                    if isinstance(val, list):
                        data = val
                        break
                else:
                    data = [data]

            if not isinstance(data, list):
                logger.debug("Ответ не является массивом")
                continue

            validated_data = validate_and_fix_enriched_objects(data)
            if not validated_data:
                logger.warning(f"Пустой результат валидации для {source_file}/{parent_id}")
                continue

            enriched = []
            for idx, obj in enumerate(validated_data, start=1):
                obj["chunk_id"] = f"{parent_id}_p{idx}"
                obj["source_file"] = source_file
                obj["category"] = meta["category"]
                obj["source_origin"] = meta["source_origin"]
                obj["document_source"] = meta["document_source"]
                enriched.append(obj)
            return enriched

        except json.JSONDecodeError as e:
            logger.warning(f"JSON ошибка (попытка {attempt+1}): {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка API (попытка {attempt+1}): {e}")
            continue

    # Все попытки исчерпаны — пробуем repair
    if last_raw:
        recovered = repair_json(last_raw)
        if recovered:
            logger.info(f"🔧 Восстановлено через repair для {source_file}/{parent_id}")
            validated_recovered = validate_and_fix_enriched_objects(recovered)
            enriched = []
            for idx, obj in enumerate(validated_recovered, start=1):
                obj["chunk_id"] = f"{parent_id}_p{idx}"
                obj["source_file"] = source_file
                obj["category"] = meta["category"]
                obj["source_origin"] = meta["source_origin"]
                obj["document_source"] = meta["document_source"]
                enriched.append(obj)
            return enriched
        else:
            log_failure(source_file, parent_id, last_raw)
    else:
        log_failure(source_file, parent_id, "No response")

    return None


# ================= ОБРАБОТКА ФАЙЛА =================

async def process_file(file_path: Path, is_html: bool):
    file_name = file_path.name
    base_name = file_path.stem
    meta = get_file_metadata(file_name, is_html)

    # Выбираем output dir
    output_dir = OUTPUT_NORMATIVE if meta["source_origin"] == "normative" else OUTPUT_OPERATIONAL
    output_dir.mkdir(parents=True, exist_ok=True)

    # Читаем файл
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = content.split(CHUNK_SEPARATOR)
    chunks = [c.strip() for c in chunks if c.strip()]

    if not chunks:
        # Если нет разделителей — весь файл как один чанк
        chunks = [content.strip()] if content.strip() else []

    if not chunks:
        logger.warning(f"Файл {file_name} пуст")
        return

    # Собираем уже обработанные parent_id
    processed_parent_ids = set()
    pattern = re.compile(rf"^{re.escape(base_name)}_(.*?)_p\d+\.json$")
    for existing_file in output_dir.glob(f"{base_name}_*_p*.json"):
        match = pattern.match(existing_file.name)
        if match:
            processed_parent_ids.add(match.group(1))

    # Определяем, какие чанки ещё не обработаны
    chunks_to_process = []
    for chunk in chunks:
        parent_id = generate_parent_chunk_id(file_name, chunk)
        if parent_id not in processed_parent_ids:
            chunks_to_process.append((parent_id, chunk))

    logger.info(f"📄 {file_name}: {len(chunks)} чанков, {len(processed_parent_ids)} обработано, {len(chunks_to_process)} новых | {meta['category']} / {meta['source_origin']}")

    if not chunks_to_process:
        return

    for parent_id, chunk in tqdm(chunks_to_process, desc=file_name):
        enriched = await enrich_chunk(chunk, file_name, meta)
        if enriched:
            for idx, obj in enumerate(enriched, start=1):
                chunk_filename = f"{base_name}_{parent_id}_p{idx}.json"
                chunk_path = output_dir / chunk_filename
                with open(chunk_path, "w", encoding="utf-8") as f:
                    json.dump(obj, f, ensure_ascii=False, indent=2)
        else:
            logger.warning(f"Не удалось обработать чанк {parent_id} из {file_name}")


# ================= ГЛАВНАЯ ФУНКЦИЯ =================

async def main():
    logger.info("=" * 60)
    logger.info("ЗАПУСК ОБРАБОТЧИКА v3 (new_data pipeline)")
    logger.info(f"Модель: {MODEL_NAME}")
    logger.info(f"markdown_data_split: {MARKDOWN_SPLIT_DIR}")
    logger.info(f"html_pages_split: {HTML_SPLIT_DIR}")
    logger.info(f"Выход normative: {OUTPUT_NORMATIVE}")
    logger.info(f"Выход operational: {OUTPUT_OPERATIONAL}")
    logger.info("=" * 60)

    # Проход 1: markdown_data (бывшие PDF)
    if MARKDOWN_SPLIT_DIR.exists():
        files = sorted(MARKDOWN_SPLIT_DIR.glob("*.md"))
        logger.info(f"\n📂 markdown_data_split: {len(files)} файлов")
        for fp in files:
            await process_file(fp, is_html=False)
    else:
        logger.warning(f"Папка {MARKDOWN_SPLIT_DIR} не найдена. Запустите сначала pre_split_for_llm.py")

    # Проход 2: html_pages (бывшие HTML)
    if HTML_SPLIT_DIR.exists():
        files = sorted(HTML_SPLIT_DIR.glob("*.md"))
        logger.info(f"\n📂 html_pages_split: {len(files)} файлов")
        for fp in files:
            await process_file(fp, is_html=True)
    else:
        logger.warning(f"Папка {HTML_SPLIT_DIR} не найдена. Запустите сначала pre_split_for_llm.py")

    logger.info("\n🏁 Все файлы обработаны")


if __name__ == "__main__":
    asyncio.run(main())