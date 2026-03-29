"""
Система детального логирования работы агентов
Записывает каждый шаг в JSON формате для отладки
"""
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AgentDebugLogger:
    """
    Логгер для детальной отладки работы агентов.
    
    Записывает в backend/logs/agent_debug/{session_id}/debug.json
    """
    
    def __init__(self, log_dir: str = "logs/agent_debug"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Проверяем, включено ли логирование
        self.enabled = os.getenv("AGENT_DEBUG_ENABLED", "false").lower() == "true"
        self.log_prompts = os.getenv("AGENT_DEBUG_LOG_PROMPTS", "false").lower() == "true"
        
        if self.enabled:
            logger.info(f"AgentDebugLogger включён, директория: {self.log_dir}")
            logger.info(f"Логирование промптов: {self.log_prompts}")
        else:
            logger.info("AgentDebugLogger выключен (AGENT_DEBUG_ENABLED=false)")
    
    def _get_session_dir(self, session_id: str) -> Path:
        """Получить директорию для сессии."""
        session_dir = self.log_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def _save_log(self, session_id: str, log_data: Dict[str, Any]):
        """Асинхронное сохранение лога."""
        if not self.enabled:
            return
        
        def save_async():
            try:
                session_dir = self._get_session_dir(session_id)
                log_file = session_dir / "debug.json"
                
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)
                
                logger.info(f"Debug log saved: {log_file}")
            except Exception as e:
                logger.error(f"Error saving debug log: {e}")
        
        # Запускаем в отдельном потоке, чтобы не блокировать основной процесс
        thread = threading.Thread(target=save_async, daemon=True)
        thread.start()
    
    def create_session_log(self, session_id: str, query: str) -> 'SessionDebugLogger':
        """Создать логгер для новой сессии."""
        return SessionDebugLogger(self, session_id, query)


class SessionDebugLogger:
    """
    Логгер для одной сессии запроса.
    """
    
    def __init__(self, parent: AgentDebugLogger, session_id: str, query: str):
        self.parent = parent
        self.session_id = session_id
        self.query = query
        self.started_at = datetime.now().isoformat()
        self.start_time = time.time()
        self.steps: List[Dict[str, Any]] = []
        self.final_answer = None
        self.final_sources_count = 0
        self.errors: List[str] = []
        self.step_counter = 0
    
    def add_step(
        self,
        component: str,
        action: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None
    ):
        """Добавить шаг выполнения."""
        self.step_counter += 1
        
        step_data = {
            "step_num": self.step_counter,
            "component": component,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "input_data": self._sanitize_data(input_data),
            "output_data": self._sanitize_data(output_data),
            "metadata": metadata or {}
        }
        
        # Добавляем промпт если включено логирование
        if prompt and self.parent.log_prompts:
            step_data["prompt"] = prompt
        
        self.steps.append(step_data)
        logger.debug(f"Step {self.step_counter}: {component}.{action} ({duration_ms:.1f}ms)")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Очистка данных для логирования (убираем лишнее)."""
        if not data:
            return {}
        
        result = {}
        for key, value in data.items():
            # Пропускаем большие объекты
            if isinstance(value, str) and len(value) > 500:
                result[key] = value[:500] + "..."
            elif isinstance(value, list) and len(value) > 20:
                result[key] = value[:20] + ["..."]
            else:
                result[key] = value
        
        return result
    
    def set_final_answer(self, answer: str, sources_count: int):
        """Установить финальный ответ."""
        self.final_answer = answer[:2000] + "..." if len(answer) > 2000 else answer
        self.final_sources_count = sources_count
    
    def add_error(self, error: str):
        """Добавить ошибку."""
        self.errors.append(error)
    
    def save(self):
        """Сохранить лог сессии."""
        total_duration_ms = (time.time() - self.start_time) * 1000
        
        log_data = {
            "session_id": self.session_id,
            "query": self.query,
            "started_at": self.started_at,
            "completed_at": datetime.now().isoformat(),
            "total_duration_ms": total_duration_ms,
            "steps_count": len(self.steps),
            "steps": self.steps,
            "final_answer": self.final_answer,
            "final_sources_count": self.final_sources_count,
            "errors": self.errors
        }
        
        self.parent._save_log(self.session_id, log_data)
    
    @contextmanager
    def step(self, component: str, action: str, input_data: Dict[str, Any], prompt: Optional[str] = None):
        """
        Контекстный менеджер для автоматического замера времени шага.
        
        Использование:
            with session_logger.step("QueryGenerator", "generate", {"query": "..."}) as step_logger:
                # выполнение кода
                output_data = {...}
                step_logger.set_output(output_data)
        """
        start_time = time.time()
        step_data = {
            "component": component,
            "action": action,
            "input_data": input_data,
            "prompt": prompt if self.parent.log_prompts else None
        }
        
        class StepContext:
            def __init__(self, parent_session, data):
                self.parent_session = parent_session
                self.data = data
                self.output_data = None
                self.metadata = {}
                self.error = None
            
            def set_output(self, output_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
                self.output_data = output_data
                self.metadata = metadata or {}
            
            def set_error(self, error: str):
                self.error = error
        
        ctx = StepContext(self, step_data)
        try:
            yield ctx
        except Exception as e:
            ctx.set_error(str(e))
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            output = ctx.output_data or {}
            if ctx.error:
                output["error"] = ctx.error
            
            self.add_step(
                component=component,
                action=action,
                input_data=input_data,
                output_data=output,
                duration_ms=duration_ms,
                metadata=ctx.metadata,
                prompt=prompt
            )


# Глобальный экземпляр
agent_debug_logger = AgentDebugLogger()


def get_debug_logger() -> AgentDebugLogger:
    """Получить глобальный логгер."""
    return agent_debug_logger
