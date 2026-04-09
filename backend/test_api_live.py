"""
Тестирование API на реальных вопросах из документа Testirovanie_II_po_TPP.docx
"""
import requests
import jwt
import time
import json

API_BASE_URL = "http://localhost:8880"
JWT_SECRET = "gZPocVPGMFSqFDBQVkHaVlSGa0c5sqtX8KYtxkcF"
USER_ID = "a1527bad-f668-45b6-8aca-82bcafa00cd9"
USER_EMAIL = "sabitovalmaz965@gmail.ru"

TEST_QUERIES = [
    {"id": 1, "query": "Сколько стоит подключение к электросетям?"},
    {"id": 2, "query": "Нет электричества как подключить?"},
    {"id": 3, "query": "Скажи какие документы мне нужны для подключения?"},
    {"id": 4, "query": "Срок подключения подскажите?"},
    {"id": 5, "query": "Как подать заявку на подключение?"},
]


def generate_jwt() -> str:
    import time
    payload = {
        "iss": "supabase",
        "sub": USER_ID,
        "role": "authenticated",
        "email": USER_EMAIL,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def analyze(answer: str, query_id: int) -> dict:
    """Проверяем ответ на запрещённые паттерны"""
    # Нормализуем: заменяем длинные тире и неразрывные пробелы
    norm = answer.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ").replace("\u202f", " ").lower()
    
    checks = {
        "нет 'обычный заявитель'": "обычный заявитель" not in norm,
        "нет 'возобновит подачу'": not ("возобновит" in norm and "подач" in norm),
        "нет 'помощь с подготовкой'": "помощь с подготовк" not in norm and "помочь с подготовк" not in norm and "поможем с подготовк" not in norm,
        "нет 'подготовить ТУ'": "подготовьте технические условия" not in norm and "подготовить ту" not in norm,
        "есть ФЛ/ИП/ЮЛ": "физическ" in norm or "фл)" in norm or "фл " in norm or "индивидуальн" in norm or " ип " in norm or " ип)" in norm,
        "есть 8-800": "8-800-234-77-00" in norm or "88002347700" in norm.replace("-", ""),
        "есть 'район' или 'ПОК'": "район" in norm or "пок " in norm or "пок)" in norm or "пункт обслуживания" in norm,
        "есть '10 рабоч' или '20 рабоч'": "10 рабоч" in norm or "20 рабоч" in norm,
        "есть 'до заключен' (оплата)": "до заключен" in norm or "до подписан" in norm,
    }
    return checks


def main():
    token = generate_jwt()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    session = requests.Session()

    print("=" * 80)
    print("ТЕСТИРОВАНИЕ API — вопросы из Testirovanie_II_po_TPP.docx")
    print("=" * 80)

    all_results = []

    for tc in TEST_QUERIES:
        print(f"\n{'='*80}")
        print(f"ВОПРОС #{tc['id']}: {tc['query']}")
        print(f"{'='*80}")

        t0 = time.time()
        resp = session.post(f"{API_BASE_URL}/query", json={"query": tc["query"]}, headers=headers, timeout=120)
        elapsed = time.time() - t0

        print(f"⏱ {elapsed:.1f}s | HTTP {resp.status_code}")

        if resp.status_code != 200:
            print(f"❌ Ошибка: {resp.text[:300]}")
            all_results.append({"id": tc["id"], "status": "error", "http": resp.status_code})
            continue

        data = resp.json()
        answer = data.get("answer", "")
        print(f"\n📝 Ответ:\n{'-'*80}")
        print(answer)
        print(f"{'-'*80}")

        checks = analyze(answer, tc["id"])
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        print(f"\n📊 Проверки ({passed}/{total}):")
        for name, ok in checks.items():
            print(f"  {'✅' if ok else '❌'} {name}")

        all_results.append({"id": tc["id"], "status": "ok", "passed": passed, "total": total, "checks": checks})
        time.sleep(2)

    # Итого
    print(f"\n{'='*80}")
    print("ИТОГО")
    print(f"{'='*80}")
    total_passed = 0
    total_checks = 0
    for r in all_results:
        if r["status"] == "ok":
            total_passed += r["passed"]
            total_checks += r["total"]
            status = "✅" if r["passed"] == r["total"] else "⚠️"
            print(f"{status} Вопрос #{r['id']}: {r['passed']}/{r['total']} проверок пройдено")
        else:
            print(f"❌ Вопрос #{r['id']}: HTTP {r['http']} ошибка")

    if total_checks > 0:
        print(f"\nОбщий результат: {total_passed}/{total_checks} ({total_passed/total_checks*100:.0f}%)")


if __name__ == "__main__":
    main()
