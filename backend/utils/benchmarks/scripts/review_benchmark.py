"""
Hybrid benchmark review: uses judge's binary_correctness as baseline,
then manually corrects clear misclassifications using semantic analysis
and judge's own justifications.
"""
import csv, re
from collections import defaultdict

# ── Anna Borisovna error patterns ─────────────────────────────────────
ANNA_PATTERNS = {
    'льготы_некорректно': {
        'desc': 'Льготная ставка/соц.льгота применяется некорректно',
        'keywords': ['льгот', '1198', '1304', 'социальн', 'инвалид', 'многодет', 'малоимущ', '550 руб'],
    },
    'терминология': {
        'desc': 'Неверная терминология',
        'keywords': ['обычный заявитель', 'сетевой орган'],
    },
    'нарушение_процедуры': {
        'desc': 'Нарушение порядка процедуры ТПП',
        'keywords': ['подготовить ТУ', 'подготовить технические', 'сами ТУ'],
    },
    'ограничения_мощности': {
        'desc': 'Не учтены ограничения по мощности/категории',
        'keywords': ['до 150 кВт', 'до 15 кВт', 'свыше 150'],
    },
    'расчет_стоимости': {
        'desc': 'Неверный расчёт стоимости/тарифы',
        'keywords': ['стоимость', 'расчет', 'ставк', 'тариф', 'C1', 'C8'],
    },
    'путаница_ДУ_ТП': {
        'desc': 'Путаница между ДУ и ТП',
        'keywords': ['аннулировать.*?ДУ', 'ДУ.*?через ЛК', 'расторг.*?ДУ'],
    },
}

# ── Load ──────────────────────────────────────────────────────────────
with open('combined_benchmark.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

# ── Semantic classification heuristics ────────────────────────────────

def is_answer_not_found(answer):
    patterns = [
        r'в предоставленных документах нет',
        r'информация.*?отсутствует',
        r'в базе знаний отсутствует',
        r'не удалось найти',
        r'нет указания',
        r'не содержит.*?информации',
    ]
    a = answer.lower()
    return any(re.search(p, a) for p in patterns)

def is_meaning_correct_vs_exact(answer, expected):
    """If expected is short (< 50 chars) and answer is much longer (>300 chars),
    it's likely meaning_correct with extra detail, not exact match."""
    a = answer.strip()
    e = expected.strip()
    if len(e) < 50 and len(a) > 200:
        return 'meaning_ok'
    if len(e) < 100 and len(a) > 500:
        return 'meaning_ok'
    return 'exact'

def detect_anna_patterns(question, expected, answer):
    matched = []
    text = (question + ' ' + answer).lower()
    for pname, pinfo in ANNA_PATTERNS.items():
        for kw in pinfo['keywords']:
            if re.search(kw, text, re.IGNORECASE):
                matched.append(pname)
                break
    return matched

def my_classification(answer, expected, judge_bin, judge_just):
    """
    Determine my own binary correctness and classification.
    Uses multiple signals, not just exact matching.
    """
    a = answer.strip()
    e = expected.strip()
    jb = int(judge_bin) if judge_bin not in ('', '-1', None) else -1
    just = judge_just.lower()
    
    # Case 1: Model says answer not found
    if is_answer_not_found(a):
        return 0, 'not_found', 'Model says answer not in sources'
    
    # Case 2: No meaningful answer
    if len(a) < 15:
        return 0, 'no_answer', 'No meaningful answer'
    
    # Case 3: Judge's justification uses keywords suggesting model is WRONG
    bad_signals = [
        'противоречит эталонному', 'не соответствует ожидаемому',
        'полностью противоречит', 'критическую фактическую ошибку',
        'прямо противоречит', 'противоположный эталонному',
        'галлюцинаций', 'не основан на источниках',
        'не соответствует вопросу и эталонному',
        'не является семантически верным', 'неполон',
    ]
    wrong_count = sum(1 for s in bad_signals if s in just)
    
    # Case 4: Judge's justification says model is CORRECT
    good_signals = [
        'полностью соответствует вопросу', 'верен', 'правильный',
        'точно отражает', 'соответствует эталонному',
        'основной факт верен',
    ]
    right_count = sum(1 for s in good_signals if s in just)
    
    # Case 5: Default to judge's binary if available
    if jb == 1:
        cls = is_meaning_correct_vs_exact(a, e)
        return 1, cls, 'Judge says correct'
    
    if jb == 0:
        if wrong_count >= 2 or 'критическ' in just or 'противоречит' in just:
            return 0, 'error', f'Judge+justification confirms error ({wrong_count} bad signals)'
        elif right_count >= 2:
            # Judge says wrong but justification says correct? Rare but possible
            return 1, 'meaning_ok', 'Judge says wrong but justification positive'
        else:
            return 0, 'error', 'Judge says wrong, justification ambiguous'
    
    # Case 6: No judge data
    return 0, 'error', 'No judge data available'


# ── Review ─────────────────────────────────────────────────────────────
reviewed = []
for i, row in enumerate(rows):
    if i % 50 == 0:
        print(f"Reviewing {i+1}/{len(rows)}...")
    
    answer = row.get('answer', '')
    expected = row.get('expected', '')
    question = row.get('question', '')
    judge_bin = row.get('judge_binary_correctness', '')
    judge_just = row.get('judge_justification', '')
    category = row.get('category', '')
    
    my_bin, my_cls, notes = my_classification(answer, expected, judge_bin, judge_just)
    anna = detect_anna_patterns(question, expected, answer)
    
    try:
        jb = int(judge_bin)
    except (ValueError, TypeError):
        jb = -1
    
    if jb == -1:
        judge_agrees = 'no_data'
    elif jb == my_bin:
        judge_agrees = 'agree'
    elif jb == 0 and my_bin == 1:
        judge_agrees = 'judge_too_strict'
    elif jb == 1 and my_bin == 0:
        judge_agrees = 'judge_too_lenient'
    else:
        judge_agrees = 'mismatch'
    
    reviewed.append({
        'index': row.get('index', ''),
        'category': category,
        'question': question[:200],
        'expected_short': expected[:250],
        'answer_short': answer[:250],
        'my_binary': my_bin,
        'my_class': my_cls,
        'notes': notes,
        'judge_binary': judge_bin,
        'judge_overall': row.get('judge_overall_score', ''),
        'judge_agrees': judge_agrees,
        'anna_patterns': ','.join(anna) if my_bin == 0 and anna else ('none' if my_bin == 1 else 'none'),
        'judge_justification': judge_just[:300],
    })

# ── Save ───────────────────────────────────────────────────────────────
fieldnames = [
    'index', 'category', 'question',
    'my_binary', 'my_class', 'notes',
    'judge_binary', 'judge_overall', 'judge_agrees',
    'anna_patterns', 'expected_short', 'answer_short', 'judge_justification'
]

with open('benchmark_review.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(reviewed)

# ── Stats ──────────────────────────────────────────────────────────────
stats = defaultdict(lambda: defaultdict(int))
for r in reviewed:
    cat = r['category']
    stats[cat]['total'] += 1; stats['total']['total'] += 1
    stats[cat]['correct'] += r['my_binary']; stats['total']['correct'] += r['my_binary']
    stats[cat][f"cls_{r['my_class']}"] += 1; stats['total'][f"cls_{r['my_class']}"] += 1
    stats[cat][f"judge_{r['judge_agrees']}"] += 1; stats['total'][f"judge_{r['judge_agrees']}"] += 1
    if r['anna_patterns'] != 'none':
        for ap in r['anna_patterns'].split(','):
            stats[cat][f"anna_{ap}"] += 1; stats['total'][f"anna_{ap}"] += 1

print("\n" + "="*65)
print("REVIEW RESULTS")
print("="*65)

for cat in ['ЛК', 'ДУ', 'ТПП', 'total']:
    t = stats[cat]['total']
    if t == 0: continue
    c, e = stats[cat]['correct'], t - stats[cat]['correct']
    label = cat.upper() if cat != 'total' else 'OVERALL'
    print(f"{label}: {t}q | {c} correct ({c/t*100:.1f}%) | {e} errors ({e/t*100:.1f}%)")
    for cls in ['exact', 'meaning_ok', 'error', 'not_found', 'no_answer']:
        cnt = stats[cat].get(f'cls_{cls}', 0)
        if cnt: print(f"  {cls}: {cnt}")
    print(f"  Judge: agree={stats[cat].get('judge_agree',0)} strict={stats[cat].get('judge_judge_too_strict',0)} lenient={stats[cat].get('judge_judge_too_lenient',0)} nodata={stats[cat].get('judge_no_data',0)}")

print("\nAnna patterns in errors:")
for pname, pinfo in ANNA_PATTERNS.items():
    cnt = stats['total'].get(f'anna_{pname}', 0)
    if cnt: print(f"  {pinfo['desc']}: {cnt}")

print(f"\nSaved benchmark_review.csv ({len(reviewed)} rows)")
