"""
Статический тест: проверка бизнес-правил в промптах
"""
import os
import sys

def main():
    print("=" * 80)
    print("СТАТИЧЕСКИЙ ТЕСТ: Проверка бизнес-правил в промптах")
    print("=" * 80)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_files = [
        os.path.join(base_dir, "backend", "prompts", "system_prompt.py"),
        os.path.join(base_dir, "backend", "prompts", "synthesis_prompt.py"),
    ]
    
    all_passed = True
    
    for prompt_file in prompt_files:
        rel_path = os.path.relpath(prompt_file, base_dir)
        print(f"\n📄 {rel_path}")
        print("-" * 80)
        
        if not os.path.exists(prompt_file):
            print(f"  ❌ Файл не найден!")
            all_passed = False
            continue
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = {
            "БИЗНЕС-ПРАВИЛА раздел": "БИЗНЕС-ПРАВИЛА" in content,
            "ФЛ/ИП/ЮЛ (ИП указан)": "Индивидуальный предприниматель" in content or "ИП" in content,
            "Запрет 'обычный заявитель'": "обычный заявитель" in content.lower() and ("НИКОГДА" in content or "НЕЛЬЗЯ" in content or "не используй" in content.lower()),
            "КЦ 8-800-234-77-00": "8-800-234-77-00" in content,
            "ПОК в районах": "район" in content.lower() and ("пункт" in content.lower() or "ПОК" in content),
            "Сроки 10/20 рабочих дней": "10 рабоч" in content or "20 рабоч" in content,
            "Оплата до договора": "до заключения договора" in content.lower() or "до подписан" in content.lower(),
            "ТУ выдаёт СО": "сетевая организация" in content.lower() and "потребитель" in content.lower(),
            "Нет помощи с документами": "НЕ помогает" in content or "только консультация" in content.lower(),
            "Запрет 'возобновит подачу'": "возобновит" in content.lower() and ("не используй" in content.lower() or "первичн" in content.lower()),
        }
        
        file_passed = True
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check_name}")
            if not result:
                file_passed = False
                all_passed = False
        
        if file_passed:
            print(f"  ✅ Все проверки пройдены ({len(checks)}/{len(checks)})")
        else:
            failed = sum(1 for v in checks.values() if not v)
            print(f"  ❌ Провалено проверок: {failed}/{len(checks)}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("❌ ЕСТЬ ПРОВАЛЕННЫЕ ПРОВЕРКИ")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
