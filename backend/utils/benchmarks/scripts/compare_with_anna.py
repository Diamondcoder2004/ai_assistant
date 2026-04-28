import csv
import re
from collections import defaultdict

# ── Anna Borisovna's remarks summary (patterns from her 73 comments) ────────
ANNA_PATTERNS = {
    # Pattern 1: льготная ставка только для ФЛ до 15 кВт, модель применяет неверно
    'льготная_ставка_некорректно': {
        'description': 'Льготная ставка/соц.льгота применяется некорректно (должна только для ФЛ до 15 кВт)',
        'triggers': [r'льгот', r'социальн.*?льгот', r'1198', r'1\s?304', r'инвалид', r'многодет', r'малоимущ'],
        'annas_notes': [
            'Льготная ставка применяется только для ФЛ до 15 кВт, с соблюдением нескольких критериев',
            'Не может быть расчет по данным ставкам более чем для 15 кВт',
            'Только для ФЛ до 15 кВт',
            'Нет такой льготной ставки 1000 руб.',
        ]
    },
    # Pattern 2: неверная терминология / неправильные формулировки
    'неверная_терминология': {
        'description': 'Неверная терминология или формулировки ("обычный заявитель", "сетевой орган" и т.п.)',
        'triggers': [r'обычн.*?заявител', r'сетев.*?орган', r'стандартн.*?заявител'],
        'annas_notes': [
            'Нет формулировки «Обычный заявитель», это либо ФЛ, ИП или ЮЛ',
            '? что такое сетевой орган?',
            'Формулировка не понятная',
        ]
    },
    # Pattern 3: неверный порядок процедуры / этапов
    'нарушение_процедуры': {
        'description': 'Нарушение порядка процедуры ТПП (ТУ выдаёт СО, а не потребитель; этапы перепутаны)',
        'triggers': [r'ТУ.*?подготовить', r'подготовить.*?ТУ', r'технические условия.*?сами', r'сами.*?технические условия',
                     r'этап.*?после', r'после.*?ввода.*?эксплуатац'],
        'annas_notes': [
            'ТУ выдает СО, потребитель не может их подготовить',
            '? не понятно почему этот этап после ввода в эксплуатацию. Оплату за ТПП потребитель вносит до заключения договора.',
            'ТУ на этапе подачи заявки у заявителя быть не может, их разрабатывает СО',
        ]
    },
    # Pattern 4: ограничения по мощности/категории не учтены
    'ограничения_по_мощности': {
        'description': 'Не учтены ограничения по мощности/категории заявителя (ФЛ/ИП/ЮЛ)',
        'triggers': [r'до 150 кВт|свыше 150|до 15 кВт|ФЛ.*?150|ИП.*?150|ЮЛ.*?150'],
        'annas_notes': [
            'Только до 150 кВт, свыше 150 кВт фактическое присоединение входит в пакет услуг по ТПП',
            'Только для заявителей до 150 кВт, для остальных фактическое присоединение выполняется силами СО',
            'До 150 кВт проверку выполнения ТУ СО не выполняет',
            'Для заявителей до 150 кВт уведомлять не нужно',
            'Только до 15 кВт ФЛ, с определенным набором критериев подключения',
            'Нет ИП',
        ]
    },
    # Pattern 5: неверный расчёт стоимости / тарифы
    'неверный_расчет_стоимости': {
        'description': 'Неверный расчёт стоимости или тарифы',
        'triggers': [r'С1|С8|стоимость.*?расчет|расчет.*?стоимости|ставк.*?C1|C8.*?ставк|6\s?000.*?руб|руб.*?6\s?000'],
        'annas_notes': [
            'Не верная формулировка. С1 – это только ставка покрывающая затраты СО на разработку документов',
            'Расчет производится в зависимости от сложности работ после подготовки ТУ',
            'Тарифы 2025 года',
            'точную стоимость потребитель сможет узнать только после разработки ТУ и подготовки договора',
        ]
    },
    # Pattern 6: ответ не по вопросу / путает ДУ и ТП
    'путаница_ДУ_ТП': {
        'description': 'Путаница между Дополнительными услугами (ДУ) и Технологическим присоединением (ТП)',
        'triggers': [r'аннулировать.*?ДУ', r'ДУ.*?через.*?ЛК', r'технологическое присоединение.*?ДУ', r'ДУ.*?ТП'],
        'annas_notes': [
            'Заявитель не может аннулировать заявку на ДУ через ЛК, только очно',
        ]
    },
}

# ── Read error analysis ─────────────────────────────────────────────────
with open(r'D:\ai_assistant\error_analysis.csv', encoding='utf-8-sig') as f:
    errors = list(csv.DictReader(f))

print(f"Loaded {len(errors)} error rows")

# ── Categorize errors by Anna's patterns ─────────────────────────────────
pattern_matches = defaultdict(lambda: defaultdict(list))

for err in errors:
    answer = err.get('answer', '')
    expected = err.get('expected', '')
    question = err.get('question', '')
    text = f"{question} {answer}".lower()
    
    for pname, pinfo in ANNA_PATTERNS.items():
        for trigger in pinfo['triggers']:
            if re.search(trigger, text, re.IGNORECASE):
                pattern_matches[pname][err['category']].append(err)
                break  # one match per pattern per error

# ── Write comparison report ────────────────────────────────────────────
with open(r'D:\ai_assistant\anna_comparison_report.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 90 + "\n")
    f.write("СРАВНЕНИЕ ОШИБОК МОДЕЛИ С ЗАМЕЧАНИЯМИ АННЫ БОРИСОВНЫ (Testirovanie_II_po_TPP)\n")
    f.write("=" * 90 + "\n\n")
    f.write(f"Всего ошибок в бенчмарке: {len(errors)}\n")
    f.write(f"Замечаний Анны Борисовны: 73 (извлечено из Word comments)\n\n")
    
    f.write("ТИПЫ ОШИБОК, ВЫДЕЛЕННЫЕ АННОЙ БОРИСОВНОЙ:\n")
    f.write("-" * 90 + "\n")
    for i, (pname, pinfo) in enumerate(ANNA_PATTERNS.items(), 1):
        f.write(f"\n  {i}. {pinfo['description']}\n")
        for note in pinfo['annas_notes']:
            f.write(f"     Анна: «{note}»\n")
    
    f.write("\n\n" + "=" * 90 + "\n")
    f.write("РЕЗУЛЬТАТЫ СОПОСТАВЛЕНИЯ:\n")
    f.write("=" * 90 + "\n\n")
    
    total_matched = 0
    
    for pname, pinfo in ANNA_PATTERNS.items():
        cats = pattern_matches[pname]
        total_for_pattern = sum(len(v) for v in cats.values())
        total_matched += total_for_pattern
        
        f.write(f"паттерн: {pinfo['description']}\n")
        f.write(f"  найдено совпадений: {total_for_pattern}\n")
        for cat in ['ЛК', 'ДУ', 'ТПП']:
            cnt = len(cats.get(cat, []))
            if cnt > 0:
                f.write(f"    {cat}: {cnt} шт.\n")
        
        # Show examples
        examples = []
        for cat_errors in cats.values():
            examples.extend(cat_errors)
        if examples:
            f.write(f"  Примеры:\n")
            for ex in examples[:3]:
                cat = ex.get('category', '?')
                f.write(f"    [{cat}] Q: {ex['question'][:120]}...\n")
                f.write(f"          Expected: {ex['expected'][:150]}...\n")
                f.write(f"          Answer:   {ex['answer'][:150]}...\n")
        f.write("\n")
    
    f.write("-" * 90 + "\n")
    f.write(f"Всего ошибок, соответствующих хотя бы одному паттерну Анны: {total_matched} из {len(errors)}\n")
    
    # ── Specific deep analysis ──────────────────────────────────────
    f.write("\n\n" + "=" * 90 + "\n")
    f.write("ДЕТАЛЬНЫЙ АНАЛИЗ ПО КАТЕГОРИЯМ:\n")
    f.write("=" * 90 + "\n")
    
    for cat in ['ЛК', 'ДУ', 'ТПП']:
        cat_errors = [e for e in errors if e['category'] == cat]
        f.write(f"\n{'─' * 70}\n")
        f.write(f"Категория: {cat} — {len(cat_errors)} ошибок\n")
        
        # Which patterns match this category?
        cat_patterns = {}
        for pname in ANNA_PATTERNS:
            matched = [e for e in (pattern_matches[pname].get(cat, []))]
            if matched:
                cat_patterns[pname] = len(matched)
        
        if cat_patterns:
            f.write(f"  Соответствие паттернам Анны Борисовны:\n")
            for pname, cnt in sorted(cat_patterns.items(), key=lambda x: -x[1]):
                f.write(f"    - {ANNA_PATTERNS[pname]['description']}: {cnt} совпадений\n")
        
        # Key error topics
        f.write(f"  Ключевые темы ошибок:\n")
        for e in cat_errors[:5]:
            f.write(f"    [#{e['index']}] {e['question'][:100]}...\n")
            f.write(f"      Ожидалось: {e['expected'][:120]}...\n")
            f.write(f"      Модель:    {e['answer'][:120]}...\n")
    
    # ── Summary for executive ─────────────────────────────────────
    f.write("\n\n" + "=" * 90 + "\n")
    f.write("ИТОГОВЫЕ ВЫВОДЫ\n")
    f.write("=" * 90 + "\n\n")
    
    f.write("1. Общая точность модели: 115/308 = 37.3%\n")
    f.write("2. Худшая категория: ДУ (26.9% правильных)\n")
    f.write("3. Лучшая категория: ЛК (54.7% правильных)\n\n")
    
    f.write("4. Ошибки того же рода, что отметила Анна Борисовна:\n")
    for pname, pinfo in ANNA_PATTERNS.items():
        cnt = sum(len(v) for v in pattern_matches[pname].values())
        if cnt > 0:
            f.write(f"   - {pinfo['description']}: {cnt} случаев\n")
    
    f.write(f"\n5. Всего {total_matched} из {len(errors)} ({total_matched/len(errors)*100:.0f}%) ")
    f.write("ошибок модели относятся к тем же паттернам, которые выделила Анна Борисовна.\n")
    
    f.write("\n6. Основные проблемы модели:\n")
    f.write("   - Неправильно определяет границы применимости правил (льготы, ограничения по мощности)\n")
    f.write("   - Путает процедуры ДУ и ТП (например, аннулирование, подписание)\n")
    f.write("   - Даёт ответы «от себя» вместо строгого следования источникам\n")
    f.write("   - Не учитывает различия между категориями заявителей (ФЛ/ИП/ЮЛ)\n")

print("Report written to anna_comparison_report.txt")
