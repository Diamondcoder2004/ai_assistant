"""
Полное тестирование API на замечания из документа Testirovanie_II_po_TPP.docx
С ручным JWT токеном
"""
import requests
import json
import time
import jwt

API_BASE_URL = "http://localhost:8880"
JWT_SECRET = "gZPocVPGMFSqFDBQVkHaVlSGa0c5sqtX8KYtxkcF"
USER_ID = "a1527bad-f668-45b6-8aca-82bcafa00cd9"
USER_EMAIL = "sabitovalmaz965@gmail.ru"

# Тестовые запросы на основе замечаний из документа
TEST_QUERIES = [
    {
        "id": 1,
        "query": "Сколько стоит подключение к электросетям?",
        "description": "Вопрос о стоимости подключения"
    },
    {
        "id": 2,
        "query": "Нет электричества как подключить?",
        "description": "Первичное подключение объекта"
    },
    {
        "id": 3,
        "query": "Скажи какие документы мне нужны для подключения?",
        "description": "Запрос списка документов для ТП"
    },
    {
        "id": 4,
        "query": "Срок подключения подскажите?",
        "description": "Вопрос о сроках технологического присоединения"
    },
    {
        "id": 5,
        "query": "Как подать заявку на подключение?",
        "description": "Порядок подачи заявки на ТП"
    }
]


def generate_jwt_token() -> str:
    """Генерируем JWT токен вручную"""
    import time
    payload = {
        "iss": "supabase",
        "sub": USER_ID,
        "role": "authenticated",
        "email": USER_EMAIL,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def test_query(session: requests.Session, test_case: dict, auth_token: str) -> dict:
    """Тестируем один запрос к API"""
    print(f"\n{'='*80}")
    print(f"ТЕСТ #{test_case['id']}: {test_case['query']}")
    print(f"Описание: {test_case['description']}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    response = session.post(
        f"{API_BASE_URL}/query",
        json={"query": test_case["query"]},
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        },
        timeout=120
    )
    
    elapsed = time.time() - start_time
    
    print(f"⏱️  Время ответа: {elapsed:.2f} сек")
    print(f"📊 Статус код: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        answer = data.get("answer", "")
        print(f"\n📝 Ответ системы:")
        print(f"{'-'*80}")
        print(answer)
        print(f"{'-'*80}")
        return {"status": "success", "answer": answer, "elapsed": elapsed}
    else:
        print(f"❌ Ошибка: {response.text[:500]}")
        return {"status": "error", "error": response.text, "elapsed": elapsed}


def analyze_response(test_case: dict, answer: str) -> dict:
    """Анализируем ответ системы на наличие проблем"""
    issues = []
    passed = []
    answer_lower = answer.lower()
    
    # Проверка 1: "обычный заявитель"
    if "обычный заявитель" in answer_lower:
        issues.append("❌ Использует запрещённый термин 'обычный заявитель'")
    else:
        passed.append("✅ Не использует 'обычный заявитель'")
    
    # Проверка 2: "возобновит подачу" для первичного подключения
    if "возобновит" in answer_lower and "подач" in answer_lower:
        issues.append("❌ Использует 'возобновит подачу' (некорректно для первичного подключения)")
    else:
        passed.append("✅ Не использует 'возобновит подачу'")
    
    # Проверка 3: Помощь с подготовкой документов
    if "поможем с подготовк" in answer_lower or "помочь с подготовк" in answer_lower:
        issues.append("❌ Предлагает помощь с подготовкой документов (запрещено)")
    else:
        passed.append("✅ Не предлагает помощь с подготовкой документов")
    
    # Проверка 4: ТУ в документах потребителя
    if "подготовьте технические условия" in answer_lower or "подготовить ту" in answer_lower:
        issues.append("❌ Говорит что потребитель готовит ТУ (неверно)")
    else:
        passed.append("✅ Не включает ТУ в документы потребителя")
    
    # Проверка 5: Номер КЦ
    if "8-800-234-77-00" in answer or "88002347700" in answer.replace("-", ""):
        passed.append("✅ Указан номер КЦ 8-800-234-77-00")
    else:
        issues.append("⚠️ Не указан номер КЦ 8-800-234-77-00")
    
    # Проверка 6: ПОК в районах
    if "район" in answer_lower or "пок " in answer_lower or "пункт обслуживания" in answer_lower:
        passed.append("✅ Упомянуты пункты обслуживания в районах РБ")
    else:
        issues.append("⚠️ Не упомянуты пункты обслуживания в районах РБ")
    
    # Проверка 7: Сроки ТУ
    if "10 рабоч" in answer_lower:
        passed.append("✅ Указан срок 10 рабочих дней (до 150 кВт)")
    elif "срок" in answer_lower:
        issues.append("⚠️ Указаны сроки, но не конкретные (10 дней для до 150 кВт)")
    
    if "20 рабоч" in answer_lower:
        passed.append("✅ Указан срок 20 рабочих дней (свыше 150 кВт)")
    
    # Проверка 8: ФЛ/ИП/ЮЛ
    if "физическ" in answer_lower or "фл " in answer_lower:
        passed.append("✅ Использует корректную категорию 'Физическое лицо'")
    
    if "индивидуальн" in answer_lower or " ип " in answer_lower or "ип," in answer_lower:
        passed.append("✅ Упомянут ИП")
    
    # Проверка 9: Оплата до договора
    if "до заключен" in answer_lower or "до подписан" in answer_lower:
        passed.append("✅ Указано что оплата до заключения договора")
    
    # Проверка 10: C1 + C8
    if "c8" in answer_lower or "последней мил" in answer_lower or "прибор учет" in answer_lower:
        passed.append("✅ Упомянута полная структура стоимости (C1 + C8 + последняя миля)")
    
    return {
        "query_id": test_case["id"],
        "query": test_case["query"],
        "passed": passed,
        "issues": issues,
        "total_checks": len(passed) + len(issues),
        "passed_count": len(passed),
        "issues_count": len(issues)
    }


def main():
    print("=" * 80)
    print("ТЕСТИРОВАНИЕ API НА ЗАМЕЧАНИЯ ИЗ ДОКУМЕНТА")
    print("Testirovanie_II_po_TPP.docx")
    print("=" * 80)
    
    # Генерируем токен
    print("\n🔐 Генерация JWT токена...")
    auth_token = generate_jwt_token()
    print(f"✅ Токен сгенерирован (длина: {len(auth_token)})")
    
    session = requests.Session()
    all_results = []
    total_passed = 0
    total_issues = 0
    
    # Тестируем каждый запрос
    for test_case in TEST_QUERIES:
        result = test_query(session, test_case, auth_token)
        
        if result["status"] == "success":
            analysis = analyze_response(test_case, result["answer"])
            all_results.append(analysis)
            total_passed += analysis["passed_count"]
            total_issues += analysis["issues_count"]
            
            # Выводим результаты анализа
            print(f"\n📊 РЕЗУЛЬТАТЫ АНАЛИЗА (Тест #{test_case['id']}):")
            print(f"{'-'*80}")
            for p in analysis["passed"]:
                print(f"  {p}")
            for i in analysis["issues"]:
                print(f"  {i}")
            print(f"{'-'*80}")
            print(f"✅ Пройдено: {analysis['passed_count']}/{analysis['total_checks']}")
            print(f"❌ Проблемы: {analysis['issues_count']}/{analysis['total_checks']}")
        
        time.sleep(1)  # Пауза между запросами
    
    # Финальное резюме
    print("\n" + "=" * 80)
    print("ИТОГОВОЕ РЕЗЮМЕ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    
    for result in all_results:
        status = "✅" if result["issues_count"] == 0 else "⚠️"
        print(f"\n{status} Тест #{result['query_id']}: {result['query']}")
        print(f"   Пройдено: {result['passed_count']}/{result['total_checks']}")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"   {issue}")
    
    print(f"\n{'='*80}")
    print(f"ОБЩАЯ СТАТИСТИКА:")
    print(f"  Всего тестов: {len(all_results)}")
    print(f"  Пройдено проверок: {total_passed}")
    print(f"  Найдено проблем: {total_issues}")
    if total_passed + total_issues > 0:
        print(f"  Процент успешных проверок: {total_passed/(total_passed+total_issues)*100:.1f}%")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
