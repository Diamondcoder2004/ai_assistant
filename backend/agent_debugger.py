"""
Agent Debugger - Пошаговое логирование работы Agentic RAG

Запись каждого шага агента в JSON файл для удобного анализа.

Запуск:
    python agent_debugger.py "ваш вопрос"
    
Пример:
    python agent_debugger.py "как определить необходимую мощность для подключения"
"""
import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
from dataclasses import dataclass, asdict, field

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """Один шаг работы агента."""
    step_num: int
    component: str
    action: str
    timestamp: str
    duration_ms: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebugSession:
    """Сессия отладки одного запроса."""
    session_id: str
    query: str
    started_at: str
    completed_at: str
    total_duration_ms: float
    steps: List[Step]
    final_answer: str
    final_sources_count: int
    errors: List[str]


class AgentDebugger:
    """Отладчик для пошагового логирования работы агента."""
    
    def __init__(self, output_dir: str = "debug_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.steps: List[Step] = []
        self.errors: List[str] = []
        self.step_num = 0
    
    def _add_step(
        self,
        component: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        duration_ms: float,
        metadata: Dict[str, Any] = None
    ):
        """Добавить шаг в лог."""
        self.step_num += 1
        
        step = Step(
            step_num=self.step_num,
            component=component,
            action=action,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            input_data=self._sanitize(input_data),
            output_data=self._sanitize(output_data),
            metadata=metadata or {}
        )
        
        self.steps.append(step)
        
        # Вывод в консоль
        logger.info(f"Шаг {step.step_num}: {component} - {action}")
        logger.info(f"  ⏱️ {duration_ms:.0f} ms")
    
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
    
    def _log_component_start(self, component: str, action: str, input_data: Dict):
        """Лог начала работы компонента."""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔹 {component}: {action}")
        logger.info(f"{'='*60}")
        if input_data:
            logger.info(f"📥 Входные данные:")
            for key, value in input_data.items():
                if isinstance(value, str) and len(value) > 100:
                    logger.info(f"   {key}: {value[:100]}...")
                else:
                    logger.info(f"   {key}: {value}")
    
    def _log_component_end(self, component: str, action: str, output_data: Dict, duration_ms: float):
        """Лог завершения работы компонента."""
        logger.info(f"✅ Завершено за {duration_ms:.0f} ms")
        if output_data:
            logger.info(f"📤 Выходные данные:")
            for key, value in output_data.items():
                if isinstance(value, str) and len(value) > 100:
                    logger.info(f"   {key}: {value[:100]}...")
                elif isinstance(value, list) and len(value) > 5:
                    logger.info(f"   {key}: [{len(value)} элементов]")
                else:
                    logger.info(f"   {key}: {value}")
    
    def trace_query_generation(self, query: str, user_hints: Dict) -> Dict:
        """Трассировка генерации поисковых запросов."""
        from agents.query_generator import QueryGeneratorAgent
        
        self._log_component_start(
            "QueryGenerator",
            "Генерация поисковых запросов",
            {"query": query, "user_hints": user_hints}
        )
        
        start = time.time()
        agent = QueryGeneratorAgent()
        result = agent.generate(query, user_hints=user_hints)
        duration_ms = (time.time() - start) * 1000
        
        # Конвертируем результат в dict
        result_dict = {
            "queries": result.queries if hasattr(result, 'queries') else result.get("queries", []),
            "search_params": result.search_params if hasattr(result, 'search_params') else result.get("search_params", {}),
            "clarification_needed": result.clarification_needed if hasattr(result, 'clarification_needed') else result.get("clarification_needed", False),
            "clarification_questions": result.clarification_questions if hasattr(result, 'clarification_questions') else result.get("clarification_questions", []),
            "confidence": result.confidence if hasattr(result, 'confidence') else result.get("confidence", 0)
        }
        
        output = result_dict.copy()
        
        self._add_step(
            component="QueryGenerator",
            action="generate",
            input_data={"query": query, "user_hints": user_hints},
            output_data=output,
            duration_ms=duration_ms
        )
        
        self._log_component_end("QueryGenerator", "generate", output, duration_ms)
        
        return result_dict
    
    def trace_search(self, queries: List[str], search_params: Dict) -> List[Dict]:
        """Трассировка поиска."""
        from tools.search_tool import SearchTool, SearchRequest
        
        self._log_component_start(
            "SearchTool",
            "Поиск в Qdrant",
            {"queries": queries, "search_params": search_params}
        )
        
        start = time.time()
        search_tool = SearchTool()
        
        all_results = []
        for query in queries:
            # SearchRequest использует отдельные параметры весов
            search_request = SearchRequest(
                query=query,
                k=search_params.get("k", 10),
                pref_weight=search_params.get("pref_weight", 0.4),
                hype_weight=search_params.get("hype_weight", 0.3),
                lexical_weight=search_params.get("lexical_weight", 0.2),
                contextual_weight=search_params.get("contextual_weight", 0.1)
            )
            query_results = search_tool.search(search_request)
            all_results.extend(query_results)
        
        duration_ms = (time.time() - start) * 1000
        
        # Ограничиваем вывод для лога (SearchResult - это объект)
        output = {
            "total_results": len(all_results),
            "top_5_sources": [
                {
                    "filename": getattr(r, "filename", "N/A"),
                    "breadcrumbs": getattr(r, "breadcrumbs", "")[:100],
                    "score_hybrid": getattr(r, "score_hybrid", 0),
                    "score_semantic": getattr(r, "score_semantic", 0),
                    "score_lexical": getattr(r, "score_lexical", 0)
                }
                for r in all_results[:5]
            ]
        }
        
        self._add_step(
            component="SearchTool",
            action="search",
            input_data={"queries": queries, "search_params": search_params},
            output_data=output,
            duration_ms=duration_ms,
            metadata={"all_results_count": len(all_results)}
        )
        
        self._log_component_end("SearchTool", "search", output, duration_ms)
        
        return all_results
    
    def trace_response_generation(
        self,
        query: str,
        sources: List[Dict],
        max_tokens: int
    ) -> str:
        """Трассировка генерации ответа."""
        from agents.response_agent import ResponseAgent
        
        self._log_component_start(
            "ResponseAgent",
            "Генерация ответа",
            {
                "query": query,
                "sources_count": len(sources),
                "max_tokens": max_tokens
            }
        )
        
        start = time.time()
        agent = ResponseAgent()
        
        # ResponseAgent.generate_response возвращает dict
        result = agent.generate_response(
            user_query=query,
            search_results=sources,
            max_tokens=max_tokens
        )
        duration_ms = (time.time() - start) * 1000
        
        # Обрабатываем и dict и объект
        if isinstance(result, dict):
            answer = result.get("answer", "")
            confidence = result.get("confidence", 0)
            sources_used = result.get("sources_count", len(sources))
        else:
            answer = result.answer if hasattr(result, 'answer') else ""
            confidence = result.confidence if hasattr(result, 'confidence') else 0
            sources_used = len(sources)
        
        output = {
            "answer_length": len(answer),
            "answer_preview": answer[:500] + "..." if len(answer) > 500 else answer,
            "sources_used": sources_used,
            "confidence": confidence
        }
        
        self._add_step(
            component="ResponseAgent",
            action="generate",
            input_data={"query": query, "sources_count": len(sources), "max_tokens": max_tokens},
            output_data=output,
            duration_ms=duration_ms
        )
        
        self._log_component_end("ResponseAgent", "generate", output, duration_ms)
        
        return answer
    
    def run_full_trace(self, query: str) -> DebugSession:
        """Полная трассировка запроса."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        started_at = datetime.now().isoformat()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 НАЧАЛО ТРАССИРОВКИ ЗАПРОСА")
        logger.info(f"{'='*70}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Query: {query}")
        logger.info(f"Time: {started_at}")
        
        try:
            # Шаг 1: Генерация запросов
            query_result = self.trace_query_generation(query, user_hints={})
            
            if query_result.get("clarification_needed"):
                logger.warning("❓ Требуется уточнение вопроса!")
                return DebugSession(
                    session_id=session_id,
                    query=query,
                    started_at=started_at,
                    completed_at=datetime.now().isoformat(),
                    total_duration_ms=0,
                    steps=self.steps,
                    final_answer="",
                    final_sources_count=0,
                    errors=["Clarification needed"]
                )
            
            queries = [q.get("text", "") if isinstance(q, dict) else str(q) for q in query_result.get("queries", [])]
            search_params = query_result.get("search_params", {})
            
            # Шаг 2: Поиск
            sources = self.trace_search(queries, search_params)
            
            # Шаг 3: Генерация ответа
            answer = self.trace_response_generation(
                query,
                sources,
                search_params.get("max_tokens", 2000)
            )
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}", exc_info=True)
            self.errors.append(str(e))
            answer = ""
            sources = []
        
        completed_at = datetime.now().isoformat()
        total_duration_ms = sum(step.duration_ms for step in self.steps)
        
        session = DebugSession(
            session_id=session_id,
            query=query,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            steps=self.steps,
            final_answer=answer,
            final_sources_count=len(sources),
            errors=self.errors
        )
        
        # Сохранение в JSON
        self._save_session(session)
        
        return session
    
    def _save_session(self, session: DebugSession):
        """Сохранение сессии в JSON файл."""
        filename = self.output_dir / f"debug_{session.session_id}.json"
        
        data = {
            "session_id": session.session_id,
            "query": session.query,
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
        print("🎯 Agent Debugger - пошаговое логирование Agentic RAG")
        print("="*70)
        print("\nИспользование:")
        print('  python agent_debugger.py "ваш вопрос"')
        print("\nПримеры:")
        print('  python agent_debugger.py "как подать заявку на ТП"')
        print('  python agent_debugger.py "какие документы нужны для подключения"')
        print("="*70)
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    print("\n" + "="*70)
    print("🎯 Agent Debugger")
    print("="*70)
    print(f"Запрос: {query}")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    debugger = AgentDebugger()
    session = debugger.run_full_trace(query)
    
    # Финальный вывод
    print("\n" + "="*70)
    print("✅ ТРАССИРОВКА ЗАВЕРШЕНА")
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
    
    print(f"\n💾 Файл: debug_logs/debug_{session.session_id}.json")
    print("="*70)


if __name__ == "__main__":
    main()
