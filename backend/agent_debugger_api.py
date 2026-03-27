"""
Agent Debugger - тестирование через реальный API

Запись каждого шага работы API с детальным логированием.

Запуск:
    python agent_debugger_api.py "ваш вопрос"
    
Пример:
    python agent_debugger_api.py "как определить необходимую мощность"
"""
import json
import time
import logging
import sys
import requests
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
from dataclasses import dataclass, asdict, field

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Конфигурация API
API_BASE_URL = "http://localhost:8880"  # Порт backend контейнера

# Supabase конфигурация для аутентификации
SUPABASE_URL = "http://46.191.174.57:8000"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzczNTc1MDkxLCJleHAiOjIwODg5MzUwOTF9.zMOszMWMS3yEzVKtLCZIVyfqukEQ0Kgwz8HzMeCWX7o"

# Токен будет получен автоматически
API_TOKEN = None


@dataclass
class APIStep:
    """Один шаг работы API."""
    step_num: int
    component: str
    action: str
    timestamp: str
    duration_ms: float
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    http_status: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebugSession:
    """Сессия отладки одного запроса."""
    session_id: str
    query: str
    api_url: str
    started_at: str
    completed_at: str
    total_duration_ms: float
    steps: List[APIStep]
    final_answer: str
    final_sources_count: int
    errors: List[str]


class APIDebugger:
    """Отладчик для тестирования через реальный API."""
    
    def __init__(self, output_dir: str = "debug_logs", api_url: str = None, api_token: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.api_url = api_url or API_BASE_URL
        self.steps: List[APIStep] = []
        self.errors: List[str] = []
        self.step_num = 0
        self.session = requests.Session()
        
        # Получаем токен
        self.api_token = api_token or self._get_or_login_token()
        
        # Добавляем токен аутентификации
        if self.api_token:
            self.session.headers.update({"Authorization": f"Bearer {self.api_token}"})
    
    def _get_or_login_token(self) -> str:
        """Получение токена через Supabase login."""
        import os
        
        # Проверяем переменные окружения
        token = os.getenv("SUPABASE_ACCESS_TOKEN")
        if token:
            logger.info("✅ Токен получен из переменных окружения")
            return token
        
        # Пробуем получить через login
        email = os.getenv("SUPABASE_TEST_EMAIL", "test@example.com")
        password = os.getenv("SUPABASE_TEST_PASSWORD", "test123456")
        
        login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Content-Type": "application/json"
        }
        payload = {"email": email, "password": password}
        
        try:
            response = requests.post(login_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                logger.info(f"✅ Токен получен через login ({email})")
                return token
            else:
                logger.warning(f"⚠️ Login не удался: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка login: {e}")
        
        # Возвращаем anon ключ как fallback (не будет работать для защищённых endpoints)
        logger.warning("⚠️ Используется anon ключ (некоторые endpoints могут быть недоступны)")
        return SUPABASE_ANON_KEY
    
    def _add_step(
        self,
        component: str,
        action: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        duration_ms: float,
        http_status: int,
        metadata: Dict[str, Any] = None
    ):
        """Добавить шаг в лог."""
        self.step_num += 1
        
        step = APIStep(
            step_num=self.step_num,
            component=component,
            action=action,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            request_data=self._sanitize(request_data),
            response_data=self._sanitize(response_data),
            http_status=http_status,
            metadata=metadata or {}
        )
        
        self.steps.append(step)
        
        # Вывод в консоль
        logger.info(f"Шаг {step.step_num}: {component} - {action}")
        logger.info(f"  ⏱️ {duration_ms:.0f} ms | HTTP {http_status}")
    
    def _sanitize(self, obj: Any) -> Any:
        """Очистка данных для JSON сериализации."""
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def _log_request(self, endpoint: str, data: Dict):
        """Лог запроса."""
        logger.info(f"\n{'='*60}")
        logger.info(f"📤 ЗАПРОС: {endpoint}")
        logger.info(f"{'='*60}")
        logger.info(f"URL: {self.api_url}{endpoint}")
        logger.info(f"Данные:")
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 100:
                logger.info(f"   {key}: {value[:100]}...")
            else:
                logger.info(f"   {key}: {value}")
    
    def _log_response(self, status: int, duration_ms: float, data: Dict):
        """Лог ответа."""
        logger.info(f"\n{'='*60}")
        logger.info(f"📥 ОТВЕТ: HTTP {status}")
        logger.info(f"{'='*60}")
        logger.info(f"⏱️ Время: {duration_ms:.0f} ms")
        if data:
            logger.info(f"Данные:")
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 200:
                    logger.info(f"   {key}: {value[:200]}...")
                elif isinstance(value, list) and len(value) > 5:
                    logger.info(f"   {key}: [{len(value)} элементов]")
                else:
                    logger.info(f"   {key}: {value}")
    
    def test_query_stream(self, query: str, session_id: str = None) -> Dict:
        """Тестирование потокового endpoint /query/stream."""
        endpoint = "/query/stream"
        url = f"{self.api_url}{endpoint}"
        
        payload = {
            "query": query,
            "session_id": session_id,
            "k": 10,
            "temperature": 0.8,
            "max_tokens": 2000
        }
        
        self._log_request(endpoint, payload)
        
        start = time.time()
        
        try:
            # SSE стриминг
            response = self.session.post(url, json=payload, stream=True)
            duration_ms = (time.time() - start) * 1000
            
            # Обработка SSE событий
            events = []
            sources = []
            answer_chunks = []
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        try:
                            data = json.loads(data_str)
                            events.append(data)
                            
                            if 'sources' in data and isinstance(data['sources'], list):
                                sources = data['sources']
                            
                            if 'token' in data:
                                answer_chunks.append(data['token'])
                            
                            if data.get('done'):
                                break
                                
                        except json.JSONDecodeError:
                            pass
            
            full_answer = ''.join(answer_chunks)
            
            response_data = {
                "events_count": len(events),
                "sources_count": len(sources),
                "answer_length": len(full_answer),
                "answer_preview": full_answer[:500] + "..." if len(full_answer) > 500 else full_answer
            }
            
            self._log_response(response.status_code, duration_ms, response_data)
            
            self._add_step(
                component="API",
                action="POST /query/stream",
                request_data=payload,
                response_data=response_data,
                duration_ms=duration_ms,
                http_status=response.status_code,
                metadata={"events": events[:5]}  # Первые 5 событий для отладки
            )
            
            return {
                "answer": full_answer,
                "sources": sources,
                "events": events
            }
            
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
            
            self._add_step(
                component="API",
                action="POST /query/stream",
                request_data=payload,
                response_data={"error": str(e)},
                duration_ms=duration_ms,
                http_status=0,
                metadata={"exception": type(e).__name__}
            )
            
            self.errors.append(str(e))
            return {"answer": "", "sources": [], "events": [], "error": str(e)}
    
    def test_query(self, query: str, session_id: str = None) -> Dict:
        """Тестирование обычного endpoint /query."""
        endpoint = "/query"
        url = f"{self.api_url}{endpoint}"
        
        payload = {
            "query": query,
            "session_id": session_id,
            "k": 10,
            "temperature": 0.8,
            "max_tokens": 2000
        }
        
        self._log_request(endpoint, payload)
        
        start = time.time()
        
        try:
            response = self.session.post(url, json=payload)
            duration_ms = (time.time() - start) * 1000
            
            response_data = response.json() if response.content else {}
            
            # Краткая сводка
            summary = {
                "http_status": response.status_code,
                "answer_length": len(response_data.get("answer", "")),
                "sources_count": len(response_data.get("sources", [])),
                "query_id": response_data.get("query_id"),
                "session_id": response_data.get("session_id")
            }
            
            self._log_response(response.status_code, duration_ms, summary)
            
            self._add_step(
                component="API",
                action="POST /query",
                request_data=payload,
                response_data=response_data,
                duration_ms=duration_ms,
                http_status=response.status_code
            )
            
            return response_data
            
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
            
            self._add_step(
                component="API",
                action="POST /query",
                request_data=payload,
                response_data={"error": str(e)},
                duration_ms=duration_ms,
                http_status=0,
                metadata={"exception": type(e).__name__}
            )
            
            self.errors.append(str(e))
            return {"error": str(e)}
    
    def test_health(self) -> Dict:
        """Тестирование health check."""
        endpoint = "/health"
        url = f"{self.api_url}{endpoint}"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🏥 Health Check: {endpoint}")
        logger.info(f"{'='*60}")
        
        start = time.time()
        
        try:
            response = self.session.get(url)
            duration_ms = (time.time() - start) * 1000
            
            logger.info(f"HTTP {response.status_code} | {duration_ms:.0f} ms")
            logger.info(f"Ответ: {response.json()}")
            
            self._add_step(
                component="API",
                action="GET /health",
                request_data={},
                response_data=response.json(),
                duration_ms=duration_ms,
                http_status=response.status_code
            )
            
            return response.json()
            
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
            self.errors.append(str(e))
            return {"error": str(e)}
    
    def test_bm25_status(self) -> Dict:
        """Тестирование статуса BM25 кэша."""
        endpoint = "/bm25/status"
        url = f"{self.api_url}{endpoint}"
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 BM25 Status: {endpoint}")
        logger.info(f"{'='*60}")
        
        start = time.time()
        
        try:
            response = self.session.get(url)
            duration_ms = (time.time() - start) * 1000
            
            logger.info(f"HTTP {response.status_code} | {duration_ms:.0f} ms")
            logger.info(f"Ответ: {response.json()}")
            
            self._add_step(
                component="API",
                action="GET /bm25/status",
                request_data={},
                response_data=response.json(),
                duration_ms=duration_ms,
                http_status=response.status_code
            )
            
            return response.json()
            
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
            self.errors.append(str(e))
            return {"error": str(e)}
    
    def run_full_test(self, query: str) -> DebugSession:
        """Полное тестирование API."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        started_at = datetime.now().isoformat()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 НАЧАЛО ТЕСТИРОВАНИЯ API")
        logger.info(f"{'='*70}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Query: {query}")
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Time: {started_at}")
        
        # Шаг 1: Health check
        logger.info(f"\n{'='*70}")
        logger.info("ШАГ 1: Health Check")
        logger.info(f"{'='*70}")
        self.test_health()
        
        # Шаг 2: BM25 статус
        logger.info(f"\n{'='*70}")
        logger.info("ШАГ 2: BM25 Status")
        logger.info(f"{'='*70}")
        self.test_bm25_status()
        
        # Шаг 3: Основной запрос (streaming)
        logger.info(f"\n{'='*70}")
        logger.info("ШАГ 3: Query Stream")
        logger.info(f"{'='*70}")
        result = self.test_query_stream(query)
        
        completed_at = datetime.now().isoformat()
        total_duration_ms = sum(step.duration_ms for step in self.steps)
        
        session = DebugSession(
            session_id=session_id,
            query=query,
            api_url=self.api_url,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            steps=self.steps,
            final_answer=result.get("answer", ""),
            final_sources_count=len(result.get("sources", [])),
            errors=self.errors
        )
        
        # Сохранение в JSON
        self._save_session(session)
        
        return session
    
    def _save_session(self, session: DebugSession):
        """Сохранение сессии в JSON файл."""
        filename = self.output_dir / f"api_debug_{session.session_id}.json"
        
        data = {
            "session_id": session.session_id,
            "query": session.query,
            "api_url": session.api_url,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "total_duration_ms": session.total_duration_ms,
            "steps_count": len(session.steps),
            "steps": [asdict(step) for step in session.steps],
            "final_answer": session.final_answer,
            "final_sources_count": session.final_sources_count,
            "errors": session.errors
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"💾 Лог сохранён: {filename.absolute()}")
        logger.info(f"{'='*70}")
        
        # Краткая сводка
        logger.info(f"\n📊 Сводка:")
        logger.info(f"  Всего шагов: {len(session.steps)}")
        logger.info(f"  Общее время: {session.total_duration_ms:.0f} ms")
        logger.info(f"  Источников: {session.final_sources_count}")
        logger.info(f"  Длина ответа: {len(session.final_answer)} символов")
        logger.info(f"  Ошибок: {len(session.errors)}")


def main():
    """Точка входа."""
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("🎯 API Debugger - тестирование через реальный API")
        print("="*70)
        print("\nИспользование:")
        print('  python agent_debugger_api.py "ваш вопрос"')
        print("\nПримеры:")
        print('  python agent_debugger_api.py "как подать заявку на ТП"')
        print('  python agent_debugger_api.py "какие документы нужны"')
        print("="*70)
        print(f"\nAPI URL: {API_BASE_URL}")
        print("="*70)
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    print("\n" + "="*70)
    print("🎯 API Debugger")
    print("="*70)
    print(f"Запрос: {query}")
    print(f"API URL: {API_BASE_URL}")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    debugger = APIDebugger()
    session = debugger.run_full_test(query)
    
    # Финальный вывод
    print("\n" + "="*70)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("="*70)
    
    if session.final_answer:
        print(f"\n📝 Ответ ({len(session.final_answer)} символов):")
        print("-"*70)
        print(session.final_answer[:2000])
        if len(session.final_answer) > 2000:
            print("...")
        print("-"*70)
    
    if session.errors:
        print(f"\n❌ Ошибки:")
        for error in session.errors:
            print(f"  - {error}")
    
    print(f"\n💾 Файл: debug_logs/api_debug_{session.session_id}.json")
    print("="*70)


if __name__ == "__main__":
    main()
