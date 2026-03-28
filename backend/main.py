"""
Agentic RAG — точка входа
"""
import logging
import argparse
import uuid
import time
from typing import Optional, List, Dict, Any

import config
from agents.search_agent import SearchAgent
from agents.response_agent import ResponseAgent
from prompts.system_prompt import get_system_prompt
from utils.bg_cache_loader import schedule_bm25_warmup

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(config.LOGS_DIR / f"agent_{config.DEFAULT_LLM_MODEL.replace('/', '_')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AgenticRAG:
    """
    Основной класс Agentic RAG системы.
    
    Объединяет всех агентов для полного цикла обработки запроса:
    1. Генерация поисковых запросов
    2. Поиск в базе знаний
    3. Формирование ответа
    """
    
    def __init__(self):
        self.search_agent = SearchAgent()
        self.response_agent = ResponseAgent()
        self.history = ""
        self.category = "не известна"
        logger.info("AgenticRAG инициализирован")
        
        # Фоновая загрузка BM25 кэша
        schedule_bm25_warmup(delay=1.0)
    
    def query(
        self,
        user_query: str,
        auto_retry: bool = True,
        history: List[Dict[str, str]] = None,
        user_hints: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Обработка запроса пользователя.

        Args:
            user_query: Вопрос пользователя
            auto_retry: Автоматическая повторная попытка поиска
            history: История диалога (список сообщений)
            user_hints: Рекомендации от пользователя (k, temperature, и т.д.)

        Returns:
            Словарь с результатом:
            - answer: текст ответа
            - clarification_needed: bool
            - clarification_questions: List[str]
            - sources: список источников
            - queries_used: использованные запросы
            - confidence: уверенность
        """
        query_id = str(uuid.uuid4())
        session_id = history[0].get("session_id", "unknown") if history else "unknown"
        start_time = time.time()
        
        logger.info(f"Запрос: '{user_query[:50]}...'")
        if user_hints:
            logger.info(f"Рекомендации от пользователя: {user_hints}")

        # Используем переданную историю или внутреннюю
        dialog_history = ""
        if history:
            for msg in history:
                role = "Пользователь" if msg["role"] == "user" else "Ассистент"
                dialog_history += f"{role}: {msg['content']}\n"
        else:
            dialog_history = self.history

        # 1. Поиск с использованием Search Agent
        search_result = self.search_agent.search(
            user_query=user_query,
            history=dialog_history,
            category=self.category,
            auto_retry=auto_retry,
            user_hints=user_hints,  # Передаём рекомендации
            query_id=query_id,
            session_id=session_id
        )
        
        # 2. Проверка необходимости уточнения
        if search_result["clarification_needed"]:
            clarification_response = self.response_agent.generate_clarification_response(
                user_query=user_query,
                clarification_questions=search_result["clarification_questions"]
            )
            
            return {
                "answer": clarification_response,
                "clarification_needed": True,
                "clarification_questions": search_result["clarification_questions"],
                "sources": [],
                "queries_used": [],
                "confidence": search_result["confidence"]
            }
        
        # 3. Генерация ответа с использованием Response Agent
        # Передаём историю диалога в ResponseAgent
        response_result = self.response_agent.generate_response(
            user_query=user_query,
            search_results=search_result["results"],
            history=dialog_history,  # ✅ Используем историю из БД
            query_id=query_id,
            session_id=session_id
        )

        # 4. Обновление истории
        self._update_history(user_query, response_result["answer"])

        # Логирование ответа
        logger.info(f"✅ LLM ответ (длина: {len(response_result['answer'])}): {response_result['answer'][:200]}...")
        logger.info(f"   Источники: {len(response_result['sources'])} шт.")
        logger.info(f"   Уверенность: {response_result['confidence']:.2f}")

        # 5. Формирование результата
        return {
            "answer": response_result["answer"],
            "clarification_needed": False,
            "clarification_questions": [],
            "sources": response_result["sources"],
            "queries_used": search_result["queries_used"],
            "search_params": search_result["search_params"],
            "confidence": response_result["confidence"],
            "reasoning": search_result.get("reasoning", "")
        }
    
    def _update_history(self, question: str, answer: str):
        """Обновление истории диалога."""
        self.history += f"Пользователь: {question}\n"
        self.history += f"Ассистент: {answer}\n\n"
        
        # Ограничение истории (последние 5 диалогов)
        lines = self.history.split("\n")
        if len(lines) > 20:
            self.history = "\n".join(lines[-20:])
    
    def set_category(self, category: str):
        """Установка категории клиента."""
        self.category = category
        logger.info(f"Категория установлена: {category}")
    
    def reset_history(self):
        """Сброс истории диалога."""
        self.history = ""
        logger.info("История диалога сброшена")
    
    def get_system_prompt(self) -> str:
        """Получение системного промпта."""
        return get_system_prompt()


def main():
    """Точка входа для консольного запуска."""
    parser = argparse.ArgumentParser(description="Agentic RAG — система поиска с LLM агентами")
    parser.add_argument("query", nargs="?", help="Вопрос пользователя")
    parser.add_argument("--category", "-c", default="не известна", help="Категория клиента")
    parser.add_argument("--no-retry", action="store_true", help="Отключить авто-повтор поиска")
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Инициализация системы
    rag = AgenticRAG()
    rag.set_category(args.category)
    
    # Интерактивный режим если вопрос не указан
    if not args.query:
        print("=" * 60)
        print("Agentic RAG — система поиска с LLM агентами")
        print("=" * 60)
        print("Введите вопрос (или 'exit' для выхода, 'reset' для сброса истории):\n")
        
        while True:
            try:
                query = input("\n❓ Вопрос: ").strip()
                
                if query.lower() in ["exit", "quit", "выход"]:
                    print("До свидания!")
                    break
                
                if query.lower() == "reset":
                    rag.reset_history()
                    print("✅ История сброшена")
                    continue
                
                if not query:
                    continue
                
                # Обработка запроса
                result = rag.query(query, auto_retry=not args.no_retry)
                
                # Вывод результата
                print("\n" + "=" * 60)
                print("💬 Ответ:")
                print(result["answer"])
                
                if result["sources"]:
                    print("\n📚 Источники:")
                    for i, src in enumerate(result["sources"], 1):
                        print(f"  {i}. {src['filename']} | {src['breadcrumbs']} | {src['category']}")
                
                if args.verbose:
                    print(f"\n🔍 Запросы: {result['queries_used']}")
                    print(f"📊 Параметры: {result.get('search_params', {})}")
                    print(f"🎯 Уверенность: {result['confidence']:.2f}")
                    if result.get("reasoning"):
                        print(f"💡 Логика: {result['reasoning']}")
                
                print("=" * 60)
                
            except KeyboardInterrupt:
                print("\n\nДо свидания!")
                break
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                if args.verbose:
                    logger.exception("Подробная ошибка:")
    
    else:
        # Одноразовый запрос
        result = rag.query(args.query, auto_retry=not args.no_retry)
        
        print("\n" + "=" * 60)
        print("💬 Ответ:")
        print(result["answer"])
        
        if result["sources"]:
            print("\n📚 Источники:")
            for i, src in enumerate(result["sources"], 1):
                print(f"  {i}. {src['filename']} | {src['breadcrumbs']} | {src['category']}")
        
        if args.verbose:
            print(f"\n🔍 Запросы: {result['queries_used']}")
            print(f"📊 Параметры: {result.get('search_params', {})}")
            print(f"🎯 Уверенность: {result['confidence']:.2f}")
        
        print("=" * 60)


if __name__ == "__main__":
    main()
