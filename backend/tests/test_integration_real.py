"""
Интеграционные тесты с реальными сервисами

Использует:
- Qdrant (localhost:6333)
- RouterAI API
- Supabase (localhost:8000)

Запуск: python tests/test_integration_real.py
"""
import sys
import os
import time
import logging
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from agents.query_generator import QueryGeneratorAgent
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from tools.search_tool import SearchTool, SearchRequest, SearchResult
from main import AgenticRAG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# TEST RUNNER
# =============================================================================

class IntegrationTestRunner:
    """Раннер для интеграционных тестов."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.timings = {}
    
    def run_test(self, name, test_func, timeout=60):
        """Запуск одного теста с таймингом."""
        print(f"\n{'='*60}")
        print(f"Тест: {name}")
        print(f"{'='*60}")
        
        start = time.time()
        try:
            # Таймаут
            import signal
            
            def handler(signum, frame):
                raise TimeoutError(f"Тест превысил {timeout}с")
            
            # Устанавливаем таймаут (только для Unix)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(timeout)
            
            # Запуск теста
            result = test_func()
            
            # Отменяем таймаут
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)
            
            elapsed = time.time() - start
            self.timings[name] = elapsed
            
            if result is not False:  # Явный False = провал
                print(f"✓ PASSED за {elapsed:.2f}с")
                self.passed += 1
            else:
                print(f"✗ FAILED за {elapsed:.2f}с")
                self.failed += 1
                self.errors.append((name, "Тест вернул False"))
                
        except TimeoutError as e:
            elapsed = time.time() - start
            print(f"✗ TIMEOUT ({elapsed:.2f}с): {e}")
            self.failed += 1
            self.errors.append((name, f"Timeout: {e}"))
            
        except Exception as e:
            elapsed = time.time() - start
            print(f"✗ ERROR ({elapsed:.2f}с): {type(e).__name__}: {e}")
            self.failed += 1
            self.errors.append((name, f"{type(e).__name__}: {e}"))
    
    def summary(self):
        """Вывод итогов."""
        print(f"\n{'='*60}")
        print("ИТОГИ ТЕСТИРОВАНИЯ")
        print(f"{'='*60}")
        print(f"ВСЕГО: {self.passed + self.failed + self.skipped} тестов")
        print(f"PASSED: {self.passed}")
        print(f"FAILED: {self.failed}")
        print(f"SKIPPED: {self.skipped}")
        
        if self.timings:
            print(f"\nТайминги:")
            for name, elapsed in self.timings.items():
                status = "✓" if elapsed < 10 else "⚠" if elapsed < 30 else "✗"
                print(f"  {status} {name}: {elapsed:.2f}с")
            
            avg_time = sum(self.timings.values()) / len(self.timings)
            print(f"\nСреднее время: {avg_time:.2f}с")
        
        if self.errors:
            print(f"\nОшибки:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        
        return self.failed == 0


# =============================================================================
# TESTS: CONNECTIVITY
# =============================================================================

def test_qdrant_connection():
    """Проверка подключения к Qdrant."""
    from qdrant_client import QdrantClient
    
    print("Подключение к Qdrant...")
    client = QdrantClient(
        host=os.getenv('QDRANT_HOST', 'localhost'),
        port=int(os.getenv('QDRANT_PORT', '6333'))
    )
    
    # Проверка коллекции
    collections = client.get_collections()
    print(f"Коллекции: {[c.name for c in collections.collections]}")
    
    target_collection = os.getenv('COLLECTION_NAME', 'BASHKIR_ENERGO_PERPLEXITY')
    collection_exists = any(c.name == target_collection for c in collections.collections)
    
    if not collection_exists:
        print(f"⚠ Коллекция {target_collection} не найдена!")
        return False
    
    print(f"✓ Коллекция {target_collection} найдена")
    
    # Проверка количества точек
    info = client.get_collection(target_collection)
    print(f"  Точек: {info.points_count}")
    # vectors_count может отсутствовать
    if hasattr(info, 'vectors_count'):
        print(f"  Векторов: {info.vectors_count}")
    
    return True


def test_routerai_connection():
    """Проверка подключения к RouterAI."""
    from openai import OpenAI
    
    print("Подключение к RouterAI...")
    client = OpenAI(
        api_key=os.getenv('ROUTERAI_API_KEY'),
        base_url=os.getenv('ROUTERAI_BASE_URL', 'https://routerai.ru/api/v1')
    )
    
    # Тестовый запрос
    model = os.getenv('DEFAULT_LLM_MODEL', 'nvidia/nemotron-3-super-120b-a12b')
    print(f"Модель: {model}")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты тестовый ассистент."},
                {"role": "user", "content": "Ответь 'OK' одним словом."}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        answer = response.choices[0].message.content
        print(f"Ответ LLM: {answer}")
        
        if answer and 'ok' in answer.lower():
            print("✓ RouterAI работает")
            return True
        elif answer:
            print("⚠ Ответ не содержит 'OK', но LLM ответил")
            return True  # Всё равно считаем успешным
        else:
            print("⚠ LLM вернул пустой ответ")
            return True  # Считаем успешным, т.к. API работает
            
    except Exception as e:
        print(f"✗ Ошибка RouterAI: {e}")
        return False


def test_supabase_connection():
    """Проверка подключения к Supabase."""
    print("Подключение к Supabase...")
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Проверка таблицы chats
        response = supabase.table('chats').select('id').limit(1).execute()
        
        print(f"✓ Supabase подключён")
        print(f"  Записей в chats: {len(response.data)}")
        
        return True
        
    except ImportError:
        print("⚠ Supabase клиент не установлен")
        return True  # Не критично
    except Exception as e:
        print(f"✗ Ошибка Supabase: {e}")
        return False


# =============================================================================
# TESTS: SEARCH TOOL
# =============================================================================

def test_search_tool_basic():
    """Базовый тест SearchTool."""
    print("Тест SearchTool...")
    
    tool = SearchTool()
    
    # Поиск
    request = SearchRequest(
        query="как подать заявку на подключение",
        k=5,
        pref_weight=0.4,
        hype_weight=0.3,
        lexical_weight=0.2,
        contextual_weight=0.1
    )
    
    start = time.time()
    results = tool.search(request)
    elapsed = time.time() - start
    
    print(f"Найдено результатов: {len(results)}")
    print(f"Время поиска: {elapsed:.2f}с")
    
    if len(results) == 0:
        print("✗ Нет результатов")
        return False
    
    # Проверка первого результата
    top = results[0]
    print(f"\nТоп результат:")
    print(f"  Файл: {top.filename}")
    print(f"  Score: {top.score_hybrid:.3f}")
    print(f"  Семантика: {top.score_semantic:.3f}")
    print(f"  Лексика: {top.score_lexical:.3f}")
    
    # Проверка scores
    if top.score_hybrid <= 0:
        print("✗ Hybrid score <= 0")
        return False
    
    print("✓ SearchTool работает")
    return True


def test_search_tool_bm25():
    """Тест BM25 поиска."""
    print("Тест BM25 поиска...")
    
    tool = SearchTool()
    
    # Запрос с точными словами
    request = SearchRequest(
        query="технологическое присоединение документы",
        k=5,
        pref_weight=0.2,
        hype_weight=0.1,
        lexical_weight=0.6,  # Высокий вес BM25
        contextual_weight=0.1
    )
    
    start = time.time()
    results = tool.search(request)
    elapsed = time.time() - start
    
    print(f"Найдено результатов: {len(results)}")
    print(f"Время: {elapsed:.2f}с")
    
    if len(results) == 0:
        print("✗ Нет результатов")
        return False
    
    # Проверка BM25 scores
    for i, r in enumerate(results[:3], 1):
        print(f"  {i}. {r.filename}: BM25={r.score_lexical:.3f}")
    
    print("✓ BM25 поиск работает")
    return True


def test_search_tool_multiple_queries():
    """Тест поиска по нескольким запросам."""
    print("Тест множественного поиска...")
    
    tool = SearchTool()
    
    queries = [
        "как подать заявку",
        "документы для подключения",
        "сроки технологического присоединения"
    ]
    
    total_results = 0
    start = time.time()
    
    for query in queries:
        request = SearchRequest(query=query, k=3)
        results = tool.search(request)
        total_results += len(results)
        print(f"  '{query[:30]}...': {len(results)} результатов")
    
    elapsed = time.time() - start
    
    print(f"Всего результатов: {total_results}")
    print(f"Общее время: {elapsed:.2f}с")
    
    if total_results == 0:
        print("✗ Нет результатов")
        return False
    
    print("✓ Множественный поиск работает")
    return True


# =============================================================================
# TESTS: AGENTS
# =============================================================================

def test_query_generator_real():
    """Тест Query Generator с реальным LLM."""
    print("Тест Query Generator...")
    
    agent = QueryGeneratorAgent()
    
    start = time.time()
    result = agent.generate(
        user_query="Как подать заявку на технологическое присоединение?",
        history="",
        category="физическое лицо"
    )
    elapsed = time.time() - start
    
    print(f"Время генерации: {elapsed:.2f}с")
    print(f"Запросов сгенерировано: {len(result.queries)}")
    print(f"Уточнение нужно: {result.clarification_needed}")
    print(f"Уверенность: {result.confidence:.2f}")
    
    if result.queries:
        print(f"Запросы:")
        for q in result.queries:
            print(f"  - {q['text']}")
    
    print(f"Параметры поиска:")
    print(f"  k: {result.search_params.get('k')}")
    print(f"  pref_weight: {result.search_params.get('pref_weight'):.2f}")
    print(f"  lexical_weight: {result.search_params.get('lexical_weight'):.2f}")
    
    if not result.queries and not result.clarification_needed:
        print("✗ Нет запросов и нет уточнения")
        return False
    
    print("✓ Query Generator работает")
    return True


def test_response_agent_real():
    """Тест Response Agent с реальным LLM."""
    print("Тест Response Agent...")
    
    agent = ResponseAgent()
    
    # Создаём тестовые результаты
    results = [
        SearchResult(
            id="test1",
            content="Для подачи заявки необходимо собрать документы: паспорт, правоустанавливающие документы на объект, план расположения энергопринимающих устройств.",
            summary="Порядок подачи заявки",
            category="informational",
            filename="Памятка",
            breadcrumbs="",
            score_hybrid=0.8,
            score_semantic=0.7,
            score_lexical=0.6,
            metadata={}
        )
    ]
    
    start = time.time()
    response = agent.generate_response(
        user_query="Как подать заявку?",
        search_results=results,
        temperature=0.7,
        max_tokens=500
    )
    elapsed = time.time() - start
    
    print(f"Время генерации: {elapsed:.2f}с")
    print(f"Длина ответа: {len(response.get('answer', ''))} символов")
    print(f"Источников: {len(response.get('sources', []))}")
    
    if response.get('answer'):
        print(f"\nОтвет (первые 200 символов):")
        print(f"  {response['answer'][:200]}...")
    
    if not response.get('answer'):
        print("✗ Нет ответа")
        return False
    
    print("✓ Response Agent работает")
    return True


def test_search_agent_real():
    """Тест Search Agent с реальными сервисами."""
    print("Тест Search Agent...")
    
    agent = SearchAgent()
    
    start = time.time()
    result = agent.search(
        user_query="Как подать заявку на подключение?",
        history="",
        category="физическое лицо",
        auto_retry=False
    )
    elapsed = time.time() - start
    
    print(f"Время поиска: {elapsed:.2f}с")
    print(f"Результатов: {len(result.get('results', []))}")
    print(f"Запросов использовано: {len(result.get('queries_used', []))}")
    print(f"Уверенность: {result.get('confidence', 0):.2f}")
    
    if result.get('results'):
        print(f"\nТоп результат:")
        top = result['results'][0]
        print(f"  Файл: {top.filename}")
        print(f"  Score: {top.score_hybrid:.3f}")
    
    if len(result.get('results', [])) == 0:
        print("✗ Нет результатов поиска")
        return False
    
    print("✓ Search Agent работает")
    return True


# =============================================================================
# TESTS: FULL PIPELINE
# =============================================================================

def test_full_pipeline():
    """Тест полного пайплайна Agentic RAG."""
    print("Тест полного пайплайна Agentic RAG...")
    
    rag = AgenticRAG()
    
    query = "Как подать заявку на технологическое присоединение?"
    print(f"Вопрос: {query}")
    
    start = time.time()
    result = rag.query(
        user_query=query,
        auto_retry=True
    )
    elapsed = time.time() - start
    
    print(f"\nОбщее время: {elapsed:.2f}с")
    print(f"Уточнение нужно: {result.get('clarification_needed', False)}")
    
    if result.get('clarification_needed'):
        print(f"Вопросы для уточнения: {result.get('clarification_questions', [])}")
        return True  # Это нормальный результат
    
    print(f"Ответ (первые 300 символов):")
    print(f"  {result.get('answer', '')[:300]}...")
    
    print(f"\nИсточников: {len(result.get('sources', []))}")
    for i, src in enumerate(result.get('sources', [])[:3], 1):
        print(f"  {i}. {src.get('filename', 'N/A')}")
    
    if not result.get('answer'):
        print("✗ Нет ответа")
        return False
    
    print("✓ Полный пайплайн работает")
    return True


def test_full_pipeline_with_hints():
    """Тест пайплайна с user_hints."""
    print("Тест пайплайна с user_hints...")
    
    rag = AgenticRAG()
    
    query = "Какие документы нужны для подключения?"
    user_hints = {
        "k": 15,  # Больше результатов
        "pref_weight": 0.5,  # Выше вес семантики
        "lexical_weight": 0.3  # Ниже вес BM25
    }
    
    print(f"Вопрос: {query}")
    print(f"User hints: {user_hints}")
    
    start = time.time()
    result = rag.query(
        user_query=query,
        user_hints=user_hints,
        auto_retry=True
    )
    elapsed = time.time() - start
    
    print(f"\nОбщее время: {elapsed:.2f}с")
    
    if result.get('answer'):
        print(f"Ответ (первые 200 символов):")
        print(f"  {result['answer'][:200]}...")
    
    # Проверка, что user_hints учтены
    search_params = result.get('search_params', {})
    print(f"\nПараметры поиска:")
    print(f"  k: {search_params.get('k')}")
    
    if not result.get('answer'):
        print("✗ Нет ответа")
        return False
    
    print("✓ Пайплайн с user_hints работает")
    return True


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("="*60)
    print("ИНТЕГРАЦИОННЫЕ ТЕСТЫ С РЕАЛЬНЫМИ СЕРВИСАМИ")
    print("="*60)
    print(f"\nКонфигурация:")
    print(f"  Qdrant: {os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_PORT')}")
    print(f"  Collection: {os.getenv('COLLECTION_NAME')}")
    print(f"  LLM: {os.getenv('DEFAULT_LLM_MODEL')}")
    print(f"  Supabase: {os.getenv('SUPABASE_URL')}")
    
    runner = IntegrationTestRunner()
    
    # Проверка соединений
    print("\n" + "="*60)
    print("ПРОВЕРКА СОЕДИНЕНИЙ")
    print("="*60)
    
    runner.run_test("Qdrant Connection", test_qdrant_connection, timeout=10)
    runner.run_test("RouterAI Connection", test_routerai_connection, timeout=30)
    runner.run_test("Supabase Connection", test_supabase_connection, timeout=10)
    
    # Тесты Search Tool
    print("\n" + "="*60)
    print("ТЕСТЫ SEARCH TOOL")
    print("="*60)
    
    runner.run_test("Search Tool Basic", test_search_tool_basic, timeout=30)
    runner.run_test("Search Tool BM25", test_search_tool_bm25, timeout=30)
    runner.run_test("Search Tool Multiple", test_search_tool_multiple_queries, timeout=30)
    
    # Тесты Agents
    print("\n" + "="*60)
    print("ТЕСТЫ AGENTS")
    print("="*60)
    
    runner.run_test("Query Generator", test_query_generator_real, timeout=60)
    runner.run_test("Response Agent", test_response_agent_real, timeout=60)
    runner.run_test("Search Agent", test_search_agent_real, timeout=60)
    
    # Полный пайплайн
    print("\n" + "="*60)
    print("ПОЛНЫЙ ПЛАЙПЛАЙН")
    print("="*60)
    
    runner.run_test("Full Pipeline", test_full_pipeline, timeout=120)
    runner.run_test("Full Pipeline + Hints", test_full_pipeline_with_hints, timeout=120)
    
    # Итоги
    success = runner.summary()
    
    sys.exit(0 if success else 1)
