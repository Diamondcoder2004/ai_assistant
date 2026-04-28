import csv
import re
from collections import defaultdict

# ── Read benchmark ──────────────────────────────────────────────
with open(r'D:\ai_assistant\new_data\benchmark_dataset.csv', encoding='utf-8-sig') as f:
    bench_rows = list(csv.DictReader(f))

# ── Read results ────────────────────────────────────────────────
with open(r'D:\ai_assistant\api_benchmarks\api_benchmark_20260421_154701\results.csv', encoding='utf-8-sig') as f:
    res_rows = list(csv.DictReader(f))

# Build lookup by question
bench_by_q = {}
for r in bench_rows:
    q = r['question'].strip()
    bench_by_q[q] = r

# ── Determine category from source_file ─────────────────────────
def get_category(source_file: str) -> str:
    s = source_file.lower()
    if 'личный кабинет' in s or 'личный' in s:
        return 'ЛК'
    elif 'дополнительных' in s or 'реализации ду' in s or 'по реализации ду' in s:
        return 'ДУ'
    elif 'тпп' in s or 'вопрос ответ по тпп' in s:
        return 'ТПП'
    return 'Неизвестно'

# ── Classification helpers ──────────────────────────────────────
NO_ANSWER_PATTERNS = [
    r'в предоставленных документах нет',
    r'информация о .* отсутствует',
    r'в базе знаний отсутствует',
    r'не удалось найти',
    r'я не могу ответить на этот вопрос',
    r'у меня нет информации',
    r'не располагаю информацией',
    r'не нашлось',
]
no_answer_re = re.compile('|'.join(NO_ANSWER_PATTERNS), re.IGNORECASE)

def classify(answer: str, expected: str, bin_correct: str) -> str:
    """
    Classify into:
    - exact_match: judge_binary_correctness=1 AND answer is concise match
    - meaning_correct: judge_binary_correctness=1 but answer is verbose/detailed
    - no_answer: model gave no substantive answer
    - answer_not_found: model explicitly said answer not in sources
    - error: model gave wrong answer
    """
    a = answer.strip() if answer else ''
    e = expected.strip() if expected else ''
    
    # Check for "answer not found" patterns
    if no_answer_re.search(a):
        return 'answer_not_found'
    
    # Check if answer is empty or too short to be meaningful
    if len(a) < 10:
        return 'no_answer'
    
    # Check binary correctness
    try:
        bc = int(bin_correct)
    except (ValueError, TypeError):
        bc = -1
    
    if bc == 1:
        # Check if answer is concise or verbose
        # If answer is significantly longer than expected, probably details differ
        if len(a) > len(e) * 3 and len(a) > 200:
            # But check if the answer is just wrapping the expected with markdown
            # Remove markdown formatting from answer for comparison
            clean_a = re.sub(r'\*\*|\*|#|`|\[|\]|\(|\)', '', a).lower()
            clean_e = e.lower()
            if clean_e in clean_a:
                return 'meaning_correct'
            return 'meaning_correct'
        return 'exact_match'
    elif bc == 0:
        # Binary wrong - but was it a meaningful attempt or no answer?
        if len(a) < 50:
            return 'no_answer'
        return 'error'
    else:
        return 'error'

# ── Process ─────────────────────────────────────────────────────
output_rows = []
stats = defaultdict(lambda: defaultdict(int))
error_details = defaultdict(list)  # category -> list of (question, answer, expected)

for res_row in res_rows:
    q = res_row['question'].strip()
    bench_row = bench_by_q.get(q)
    
    if bench_row is None:
        continue
    
    source_file = bench_row['source_file']
    category = get_category(source_file)
    
    classification = classify(
        answer=res_row.get('answer', ''),
        expected=res_row.get('expected', ''),
        bin_correct=res_row.get('judge_binary_correctness', '')
    )
    
    # Build output row
    out_row = dict(res_row)
    out_row['source_file'] = source_file
    out_row['category'] = category
    out_row['classification'] = classification
    output_rows.append(out_row)
    
    # Stats
    stats[category][classification] += 1
    stats['total'][classification] += 1
    stats[category]['total'] += 1
    stats['total']['total'] += 1
    
    # Track errors/not_found for analysis
    if classification in ('error', 'answer_not_found', 'no_answer'):
        error_details[category].append({
            'category': category,
            'index': res_row.get('index', ''),
            'question': q,
            'expected': bench_row['expected_answer'],
            'answer': res_row.get('answer', '')[:300],
            'classification': classification,
            'judge_binary': res_row.get('judge_binary_correctness', ''),
            'judge_overall': res_row.get('judge_overall_score', ''),
            'judge_justification': res_row.get('judge_justification', '')[:300],
        })

# ── Write combined CSV ──────────────────────────────────────────
fieldnames = list(res_rows[0].keys()) + ['source_file', 'category', 'classification']
with open(r'D:\ai_assistant\combined_benchmark.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

class_labels = {
    'exact_match': 'Exact match',
    'meaning_correct': 'Meaning correct, details differ',
    'error': 'Error',
    'answer_not_found': 'Answer not found in sources',
    'no_answer': 'No answer',
}

# ── Save error details for further analysis ─────────────────────
with open(r'D:\ai_assistant\error_analysis.csv', 'w', encoding='utf-8-sig', newline='') as f:
    fieldnames = ['category', 'index', 'question', 'expected', 'answer', 'classification', 
                  'judge_binary', 'judge_overall', 'judge_justification']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for cat, errs in error_details.items():
        for e in errs:
            writer.writerow(e)

# ── Save statistics report ─────────────────────────────────────
with open(r'D:\ai_assistant\statistics_report.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("STATISTICS BY CATEGORY\n")
    f.write("=" * 80 + "\n")
    
    for cat in ['ЛК', 'ДУ', 'ТПП']:
        total = stats[cat]['total']
        f.write(f"\ncategory: {cat} (total questions: {total})\n")
        f.write("-" * 60 + "\n")
        for cls in ['exact_match', 'meaning_correct', 'error', 'answer_not_found', 'no_answer']:
            cnt = stats[cat][cls]
            pct = cnt / total * 100 if total > 0 else 0
            label = class_labels[cls]
            f.write(f"  {label:<45} {cnt:>4}  ({pct:>5.1f}%)\n")
        
        correct = stats[cat]['exact_match'] + stats[cat]['meaning_correct']
        f.write(f"  {'TOTAL CORRECT (exact + meaning)':<45} {correct:>4}  ({correct/total*100:>5.1f}%)\n")
    
    f.write(f"\nOVERALL (total questions: {stats['total']['total']})\n")
    f.write("=" * 60 + "\n")
    for cls in ['exact_match', 'meaning_correct', 'error', 'answer_not_found', 'no_answer']:
        cnt = stats['total'][cls]
        pct = cnt / stats['total']['total'] * 100 if stats['total']['total'] > 0 else 0
        f.write(f"  {class_labels[cls]:<45} {cnt:>4}  ({pct:>5.1f}%)\n")
    
    correct_total = stats['total']['exact_match'] + stats['total']['meaning_correct']
    f.write(f"  {'TOTAL CORRECT':<45} {correct_total:>4}  ({correct_total/stats['total']['total']*100:>5.1f}%)\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("ERROR ANALYSIS BY CATEGORY\n")
    f.write("=" * 80 + "\n")
    
    for cat in ['ЛК', 'ДУ', 'ТПП']:
        errs = error_details[cat]
        f.write(f"\nCategory: {cat} - {len(errs)} errors/not-found\n")
        f.write("-" * 60 + "\n")
        for e in errs:
            f.write(f"  [#{e['index']}] [{e['classification']}] {e['question'][:120]}\n")
            f.write(f"    Expected: {e['expected'][:200]}\n")
            f.write(f"    Answer:   {e['answer'][:200]}\n")
            f.write(f"    Judge:    bin={e['judge_binary']}, overall={e['judge_overall']}\n")
            f.write(f"    Justification: {e['judge_justification'][:200]}\n")
            f.write("\n")

print("Files written: combined_benchmark.csv, error_analysis.csv, statistics_report.txt")
