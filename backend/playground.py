"""
Playground для тестирования и отладки компонентов Agentic RAG

Запуск:
    python playground.py
    
Использование:
    1. Раскомментировать нужный тест
    2. Запустить скрипт
    3. Получить детальный лог работы каждого компонента
"""
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Настраиваем детальное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(f'logs/playground_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# =============================================================================
# TEST 1: Query Generator
# =============================================================================

def test_query_generator():
    """Тестирование генерации поисковых запросов."""
    from agents.query_generator import QueryGeneratorAgent
    
    print("\n" + "="*60)
    print("ТЕСТ 1: Query Generator")
    print("="*60)
    
    agent = QueryGeneratorAgent()
    
    test_queries = [
        "Как определить необходимую мощность для подключения?",
        "Какие документы нужны для технологического присоединения?",
        "Сколько стоит подключение к электросети?",
    ]
    
    for query in test_queries:
        print(f"\n📝 Запрос: {query}")
        print("-"*60)
        
        start = time.time()
        result = agent.generate(query)
        elapsed = time.time() - start
        
        print(f"✅ Время: {elapsed:.2f} сек")
        print(f"📊 Параметры поиска:")
        print(f"   - k: {result.get('search_params', {}).get('k')}")
        print(f"   - weights: {result.get('search_params', {}).get('weights')}")
        print(f"   - strategy: {result.get('search_params', {}).get('strategy')}")
        print(f"🔍 Сгенерированные запросы:")
        for i, q in enumerate(result.get('queries', []), 1):
            print(f"   {i}. {q}")
        
        if result.get('clarification_needed'):
            print(f"❓ Требуется уточнение: {result.get('clarification_questions')}")
    
    return "Query Generator: OK"


# =============================================================================
# TEST 2: Search Tool
# =============================================================================

def test_search_tool():
    """Тестирование поискового инструмента."""
    from tools.search_tool import SearchTool, SearchRequest
    from utils.router_embedding import RouterAIEmbeddings
    
    print("\n" + "="*60)
    print("ТЕСТ 2: Search Tool")
    print("="*60)
    
    # Инициализация эмбеддингов
    print("\n🔧 Инициализация эмбеддингов...")
    embeddings = RouterAIEmbeddings()
    
    # Тестовый запрос
    test_query = "как определить необходимую мощность для подключения"
    print(f"📝 Запрос: {test_query}")
    
    # Генерация эмбеддинга
    print("\n📊 Генерация эмбеддинга...")
    start = time.time()
    embedding = embeddings.embed_query(test_query)
    embed_time = time.time() - start
    print(f"✅ Эмбеддинг: {len(embedding)} измерений, время: {embed_time:.2f} сек")
    
    # Поиск
    print("\n🔍 Поиск в Qdrant...")
    search_tool = SearchTool()
    
    search_request = SearchRequest(
        query=test_query,
        k=10,
        weights={"pref": 0.4, "hype": 0.3, "contextual": 0.3},
        strategy="concat"
    )
    
    start = time.time()
    results = search_tool.search(search_request)
    search_time = time.time() - start
    
    print(f"✅ Найдено результатов: {len(results)}")
    print(f"⏱️ Время поиска: {search_time:.2f} сек")
    
    print(f"\n📚 Топ-5 результатов:")
    for i, hit in enumerate(results[:5], 1):
        print(f"\n   {i}. {hit.get('filename', 'N/A')}")
        print(f"      Score: {hit.get('score_hybrid', 0):.3f}")
        print(f"      Breadcrumbs: {hit.get('breadcrumbs', '')[:100]}")
        print(f"      Summary: {hit.get('summary', '')[:150]}...")
    
    return "Search Tool: OK"


# =============================================================================
# TEST 3: Response Agent
# =============================================================================

def test_response_agent():
    """Тестирование генерации ответа."""
    from agents.response_agent import ResponseAgent
    from tools.search_tool import SearchTool, SearchRequest
    
    print("\n" + "="*60)
    print("ТЕСТ 3: Response Agent")
    print("="*60)
    
    agent = ResponseAgent()
    
    # Тестовый запрос и результаты поиска
    test_query = "как определить необходимую мощность для подключения"
    
    print(f"\n📝 Запрос: {test_query}")
    
    # Получаем результаты поиска
    print("\n🔍 Получение результатов поиска...")
    search_tool = SearchTool()
    search_request = SearchRequest(
        query=test_query,
        k=5,
        weights={"pref": 0.4, "hype": 0.3, "contextual": 0.3},
        strategy="concat"
    )
    search_results = search_tool.search(search_request)
    print(f"✅ Найдено {len(search_results)} результатов")
    
    # Генерация ответа
    print("\n✍️ Генерация ответа...")
    start = time.time()
    
    result = agent.generate(
        query=test_query,
        sources=search_results,
        max_tokens=500  # Короткий ответ для теста
    )
    
    elapsed = time.time() - start
    
    print(f"✅ Время генерации: {elapsed:.2f} сек")
    print(f"📊 Длина ответа: {len(result.get('answer', ''))} символов")
    print(f"\n📝 Ответ:")
    print("-"*60)
    print(result.get('answer', '')[:1000])
    if len(result.get('answer', '')) > 1000:
        print("...")
    print("-"*60)
    
    return "Response Agent: OK"


# =============================================================================
# TEST 4: Full Agentic RAG Pipeline
# =============================================================================

def test_full_pipeline():
    """Тестирование полного цикла Agentic RAG."""
    from main import AgenticRAG
    
    print("\n" + "="*60)
    print("ТЕСТ 4: Full Agentic RAG Pipeline")
    print("="*60)
    
    rag = AgenticRAG()
    
    test_query = "как определить необходимую мощность для подключения к электросети"
    print(f"\n📝 Запрос: {test_query}")
    print("-"*60)
    
    start = time.time()
    result = rag.query(test_query, auto_retry=True)
    total_time = time.time() - start
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ")
    print("="*60)
    
    print(f"\n⏱️ Общее время: {total_time:.2f} сек")
    
    print(f"\n🔍 Поисковые запросы:")
    for i, q in enumerate(result.get('queries_generated', []), 1):
        print(f"   {i}. {q}")
    
    print(f"\n📊 Параметры поиска:")
    params = result.get('search_params', {})
    print(f"   - k: {params.get('k')}")
    print(f"   - strategy: {params.get('strategy')}")
    print(f"   - weights: {params.get('weights')}")
    
    print(f"\n📚 Источники: {len(result.get('sources', []))} шт.")
    for i, src in enumerate(result.get('sources', [])[:3], 1):
        print(f"   {i}. {src.get('filename', 'N/A')} (score: {src.get('score_hybrid', 0):.3f})")
    
    print(f"\n✍️ Ответ ({len(result.get('answer', ''))} символов):")
    print("-"*60)
    answer = result.get('answer', '')
    print(answer[:1500])
    if len(answer) > 1500:
        print("...")
    print("-"*60)
    
    print(f"\n🎯 Confidence: {result.get('confidence', 0):.2f}")
    
    if result.get('clarification_needed'):
        print(f"\n❓ Требуется уточнение:")
        for q in result.get('clarification_questions', []):
            print(f"   - {q}")
    
    return "Full Pipeline: OK"


# =============================================================================
# TEST 5: Error Handling - Long Query
# =============================================================================

def test_long_query():
    """Тестирование обработки длинного запроса."""
    from main import AgenticRAG
    
    print("\n" + "="*60)
    print("ТЕСТ 5: Long Query Handling")
    print("="*60)
    
    # Очень длинный запрос
    long_query = "Как определить необходимую мощность для подключения к электросети " * 20
    print(f"\n📝 Длинный запрос ({len(long_query)} символов):")
    print(long_query[:200] + "...")
    
    rag = AgenticRAG()
    
    start = time.time()
    try:
        result = rag.query(long_query, auto_retry=True)
        elapsed = time.time() - start
        
        print(f"\n✅ Запрос обработан за {elapsed:.2f} сек")
        print(f"📊 Ответ: {len(result.get('answer', ''))} символов")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ Ошибка через {elapsed:.2f} сек: {e}")
        import traceback
        traceback.print_exc()
    
    return "Long Query Test: Complete"


# =============================================================================
# TEST 6: Error Handling - Special Characters
# =============================================================================

def test_special_characters():
    """Тестирование обработки специальных символов."""
    from main import AgenticRAG
    
    print("\n" + "="*60)
    print("ТЕСТ 6: Special Characters Handling")
    print("="*60)
    
    test_cases = [
        ("Эмодзи", "Как подключить дом к электросети? 🏠⚡"),
        ("Кавычки", 'Как подать заявку на "технологическое присоединение"?'),
        ("Слэши", "Что такое ТП/ТП-1?"),
        ("Цифры", "Сколько стоит подключение 15 кВт?"),
    ]
    
    rag = AgenticRAG()
    
    for name, query in test_cases:
        print(f"\n📝 Тест: {name}")
        print(f"   Запрос: {query}")
        
        start = time.time()
        try:
            result = rag.query(query, auto_retry=False)
            elapsed = time.time() - start
            print(f"   ✅ Успешно за {elapsed:.2f} сек")
            print(f"   📊 Ответ: {len(result.get('answer', ''))} символов")
        except Exception as e:
            elapsed = time.time() - start
            print(f"   ❌ Ошибка через {elapsed:.2f} сек: {e}")
    
    return "Special Characters Test: Complete"


# =============================================================================
# TEST 7: Timing Statistics
# =============================================================================

def test_timing_stats():
    """Тестирование сбора статистики таймингов."""
    from utils.timing import timing_stats, TimingStatistics
    from main import AgenticRAG
    
    print("\n" + "="*60)
    print("ТЕСТ 7: Timing Statistics")
    print("="*60)
    
    # Сброс статистики
    timing_stats.reset()
    
    rag = AgenticRAG()
    
    # Выполняем несколько запросов
    test_queries = [
        "Как подать заявку на ТП?",
        "Какие документы нужны?",
        "Сколько стоит подключение?",
    ]
    
    print("\n📊 Выполнение запросов для сбора статистики...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. {query}")
        result = rag.query(query, auto_retry=False)
        print(f"   ✅ {len(result.get('sources', []))} источников, {len(result.get('answer', ''))} символов")
    
    # Вывод статистики
    print("\n" + "="*60)
    print("СТАТИСТИКА ТАЙМИНГОВ")
    print("="*60)
    
    stats = timing_stats.get_stats()
    
    print(f"\n📈 Операции:")
    for op_name, op_stats in stats.get('operations', {}).items():
        print(f"\n   {op_name}:")
        print(f"      Вызовов: {op_stats.get('call_count')}")
        print(f"      Среднее время: {op_stats.get('avg_time_ms', 0):.0f} ms")
        print(f"      Мин/Макс: {op_stats.get('min_time_ms', 0):.0f} / {op_stats.get('max_time_ms', 0):.0f} ms")
    
    print(f"\n📊 Запросы:")
    for req in stats.get('recent_requests', [])[-3:]:
        print(f"   {req.get('method')} {req.get('path')}: {req.get('total_time_ms', 0):.0f} ms")
    
    return "Timing Stats: OK"


# =============================================================================
# TEST 8: Database Operations
# =============================================================================

async def test_database_operations_async():
    """Тестирование работы с базой данных (Supabase)."""
    from api.database import save_chat_to_supabase, get_chat_history
    import uuid
    
    print("\n" + "="*60)
    print("ТЕСТ 8: Database Operations")
    print("="*60)
    
    # Тестовые данные
    user_id = "test_user_" + str(uuid.uuid4())[:8]
    session_id = "test_session_" + str(uuid.uuid4())[:8]
    question = "Тестовый вопрос для проверки БД"
    answer = "Это тестовый ответ для проверки сохранения в базу данных Supabase."
    parameters = {
        "k": 10,
        "temperature": 0.8,
        "max_tokens": 2000,
        "min_score": 0.0,
        "query_id": str(uuid.uuid4())
    }
    sources = [
        {
            "chunk_id": "test_chunk_1",
            "filename": "test_file.md",
            "breadcrumbs": "Тест > Раздел",
            "summary": "Тестовое краткое содержание",
            "content": "Тестовый контент",
            "category": "test",
            "score_hybrid": 0.95,
            "score_semantic": 0.90,
            "score_lexical": 0.85
        }
    ]
    
    print(f"\n📊 Тестовые данные:")
    print(f"   User ID: {user_id}")
    print(f"   Session ID: {session_id}")
    print(f"   Question: {question}")
    print(f"   Answer: {answer[:50]}...")
    
    # Сохранение
    print("\n💾 Сохранение в Supabase...")
    start = time.time()
    result = await save_chat_to_supabase(
        user_id=user_id,
        session_id=session_id,
        question=question,
        answer=answer,
        parameters=parameters,
        sources=sources
    )
    save_time = time.time() - start
    
    if result:
        print(f"✅ Успешно за {save_time:.2f} сек")
        chat_id = result.data[0]['id'] if result.data else 'N/A'
        print(f"   Chat ID: {chat_id}")
    else:
        print(f"❌ Ошибка сохранения")
    
    # Чтение истории
    print("\n📖 Чтение истории сессии...")
    start = time.time()
    history = await get_chat_history(session_id, limit=10)
    read_time = time.time() - start
    
    print(f"✅ Прочитано за {read_time:.2f} сек")
    print(f"   Сообщений в истории: {len(history)//2}")
    
    return "Database Operations: Complete"


def test_database_operations():
    """Обёртка для async теста."""
    return asyncio.run(test_database_operations_async())


# =============================================================================
# MAIN
# =============================================================================

import asyncio

if __name__ == "__main__":
    
    print("\n" + "="*60)
    print("🎮 AGENTIC RAG PLAYGROUND")
    print("="*60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Логирование: logs/playground_*.log")
    print("="*60)
    
    # Выберите тесты для запуска
    tests = [
        # (Название, Функция, Включено)
        ("Query Generator", test_query_generator, False),
        ("Search Tool", test_search_tool, False),
        ("Response Agent", test_response_agent, False),
        ("Full Pipeline", test_full_pipeline, True),  # <-- ИЗМЕНИТЬ НА True для запуска
        ("Long Query", test_long_query, False),
        ("Special Characters", test_special_characters, False),
        ("Timing Stats", test_timing_stats, False),
        ("Database", test_database_operations, False),
    ]
    
    results = []
    
    for name, func, enabled in tests:
        if enabled:
            try:
                print(f"\n▶️ Запуск: {name}")
                result = func()
                results.append(f"✅ {name}: {result}")
            except Exception as e:
                import traceback
                error_msg = f"❌ {name}: {e}"
                results.append(error_msg)
                print(error_msg)
                traceback.print_exc()
        else:
            print(f"⏭️ Пропущено: {name}")
    
    # Итоговый отчёт
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЁТ")
    print("="*60)
    for result in results:
        print(result)
    
    print("\n" + "="*60)
    print(f"Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
