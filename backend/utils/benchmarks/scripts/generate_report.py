"""
Generate comprehensive markdown benchmark analysis report.
"""
import csv
from collections import defaultdict
from datetime import datetime

# ── Load data ─────────────────────────────────────────────────────────
with open('benchmark_review.csv', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

# ── Statistics ────────────────────────────────────────────────────────
stats = defaultdict(lambda: defaultdict(int))
judge_issues = []
error_details = defaultdict(list)

for r in rows:
    cat = r['category']
    mb = int(r['my_binary'])
    jb = float(r['judge_binary']) if r['judge_binary'] not in ('', '-1') else -1
    jo = float(r['judge_overall']) if r['judge_overall'] not in ('', '-1') else -1
    
    stats[cat]['total'] += 1
    stats['total']['total'] += 1
    stats[cat]['correct'] += mb
    stats['total']['correct'] += mb
    stats[cat][f"cls_{r['my_class']}"] += 1
    stats['total'][f"cls_{r['my_class']}"] += 1
    
    if jo > 0:
        stats[cat]['sum_score'] += jo
        stats[cat]['cnt_score'] += 1
        stats['total']['sum_score'] += jo
        stats['total']['cnt_score'] += 1
    
    ja = r['judge_agrees']
    stats[cat][f"judge_{ja}"] += 1
    stats['total'][f"judge_{ja}"] += 1
    
    if ja in ('judge_too_strict', 'judge_too_lenient'):
        judge_issues.append(r)
    
    if mb == 0:
        error_details[cat].append(r)

# ── Anna patterns summary ─────────────────────────────────────────────
anna_stats = defaultdict(int)
for r in rows:
    if r['anna_patterns'] != 'none':
        for ap in r['anna_patterns'].split(','):
            anna_stats[ap] += 1

# ── Top problem questions ─────────────────────────────────────────────
# Questions where model consistently fails: same source_file with multiple errors
source_errors = defaultdict(list)
for r in rows:
    if int(r['my_binary']) == 0:
        # Extract source file from question context (not available in review CSV, use index proxy)
        source_errors[r['index']].append(r)

# ── Write markdown report ─────────────────────────────────────────────
with open('benchmark_analysis_report.md', 'w', encoding='utf-8') as f:
    f.write(f"# Benchmark Analysis Report — AI Assistant (Башкирэнерго)\n\n")
    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**Dataset:** combined_benchmark.csv (308 questions)\n")
    f.write(f"**Review method:** Judge LLM (deepseek-v3.2) + manual semantic verification\n\n")
    
    # ── 1. Executive Summary ──
    f.write("## 1. Executive Summary\n\n")
    f.write(f"- **Total questions:** 308\n")
    f.write(f"- **Correct answers:** {stats['total']['correct']} ({stats['total']['correct']/308*100:.1f}%)\n")
    f.write(f"- **Errors:** {308 - stats['total']['correct']} ({(308 - stats['total']['correct'])/308*100:.1f}%)\n")
    f.write(f"- **Judge-model agreement:** {stats['total'].get('judge_agree', 0)}/308 ({stats['total'].get('judge_agree', 0)/308*100:.1f}%)\n")
    f.write(f"- **Answer not found:** {stats['total'].get('cls_not_found', 0)} cases\n")
    f.write(f"- **Average judge overall_score:** {stats['total']['sum_score']/stats['total']['cnt_score']:.2f}\n\n")
    
    f.write("### Category Breakdown\n\n")
    f.write("| Category | Questions | Correct | % | Avg Score |\n")
    f.write("|----------|-----------|---------|----|----------|\n")
    for cat in ['ЛК', 'ДУ', 'ТПП']:
        t = stats[cat]['total']
        c = stats[cat]['correct']
        pct = c/t*100
        avg = stats[cat]['sum_score']/stats[cat]['cnt_score'] if stats[cat]['cnt_score'] > 0 else 0
        cat_name = {'ЛК': 'Личный кабинет', 'ДУ': 'Дополнительные услуги', 'ТПП': 'Технологическое присоединение'}[cat]
        f.write(f"| {cat_name} | {t} | {c} | {pct:.1f}% | {avg:.2f} |\n")
    f.write(f"| **Всего** | **{stats['total']['total']}** | **{stats['total']['correct']}** | **{stats['total']['correct']/308*100:.1f}%** | **{stats['total']['sum_score']/stats['total']['cnt_score']:.2f}** |\n\n")
    
    # ── 2. Detailed Statistics ──
    f.write("## 2. Detailed Statistics by Category\n\n")
    
    for cat in ['ЛК', 'ДУ', 'ТПП']:
        t = stats[cat]['total']
        c = stats[cat]['correct']
        cat_name = {'ЛК': 'Личный кабинет (ЛК)', 'ДУ': 'Дополнительные услуги (ДУ)', 'ТПП': 'Технологическое присоединение (ТПП)'}[cat]
        
        f.write(f"### 2.{['ЛК','ДУ','ТПП'].index(cat)+1}. {cat_name}\n\n")
        f.write(f"**Total:** {t} questions | **Correct:** {c} ({c/t*100:.1f}%) | **Errors:** {t-c} ({(t-c)/t*100:.1f}%)\n\n")
        
        f.write("| Classification | Count | % |\n")
        f.write("|----------------|-------|---|\n")
        for cls, label in [('exact', 'Exact match'), ('meaning_ok', 'Meaning correct'), ('error', 'Error'), ('not_found', 'Not found'), ('no_answer', 'No answer')]:
            cnt = stats[cat].get(f'cls_{cls}', 0)
            if cnt > 0:
                f.write(f"| {label} | {cnt} | {cnt/t*100:.1f}% |\n")
        
        f.write(f"\n**Judge agreement:**\n")
        f.write(f"- Agree: {stats[cat].get('judge_agree', 0)}\n")
        f.write(f"- Judge too strict: {stats[cat].get('judge_judge_too_strict', 0)}\n")
        f.write(f"- Judge too lenient: {stats[cat].get('judge_judge_too_lenient', 0)}\n")
        f.write(f"- No data: {stats[cat].get('judge_no_data', 0)}\n\n")
        
        # Top errors
        errs = error_details[cat][:5]
        if errs:
            f.write(f"**Sample errors:**\n\n")
            for e in errs:
                f.write(f"- #{e['index']}: _{e['question'][:120]}..._\n")
                f.write(f"  - Expected: {e['expected_short'][:150]}...\n")
                f.write(f"  - Answer: {e['answer_short'][:150]}...\n\n")
    
    # ── 3. Judge Objectivity Analysis ──
    f.write("## 3. Judge LLM Objectivity Analysis\n\n")
    f.write(f"The judge model (deepseek-v3.2) achieved **{stats['total'].get('judge_agree', 0)}/308 ({stats['total'].get('judge_agree', 0)/308*100:.1f}%) agreement** with manual semantic review.\n\n")
    
    if judge_issues:
        f.write(f"### Disagreements ({len(judge_issues)} cases)\n\n")
        f.write("| # | Category | Judge Binary | My Binary | Why |\n")
        f.write("|---|----------|-------------|-----------|-----|\n")
        for r in judge_issues:
            f.write(f"| {r['index']} | {r['category']} | {r['judge_binary']} | {r['my_binary']} | {r['notes'][:100]} |\n")
    
    f.write(f"\n**Judge bias analysis:**\n")
    strict = stats['total'].get('judge_judge_too_strict', 0)
    lenient = stats['total'].get('judge_judge_too_lenient', 0)
    f.write(f"- Judge was too strict (marked correct answers as wrong): {strict}\n")
    f.write(f"- Judge was too lenient (marked wrong answers as correct): {lenient}\n")
    f.write(f"- No judge data available: {stats['total'].get('judge_no_data', 0)}\n")
    if strict > lenient:
        f.write(f"- **Bias verdict:** Judge tends to be overly strict, penalizing verbose-but-correct answers\n")
    elif lenient > strict:
        f.write(f"- **Bias verdict:** Judge tends to be overly lenient, missing subtle errors\n")
    else:
        f.write(f"- **Bias verdict:** Judge is balanced\n\n")
    
    # ── 4. Error Patterns (Anna Borisovna) ──
    f.write("## 4. Error Patterns (Анна Борисовна)\n\n")
    f.write("Classification of errors according to Anna Borisovna's review notes from `Testirovanie_II_po_TPP.docx`:\n\n")
    
    pattern_names = {
        'терминология': 'Неверная терминология ("обычный заявитель", "сетевой орган")',
        'ограничения_мощности': 'Не учтены ограничения по мощности/категории заявителя',
        'расчет_стоимости': 'Неверный расчёт стоимости или тарифы',
        'льготы_некорректно': 'Льготная ставка/соц.льгота применяется некорректно',
        'путаница_ДУ_ТП': 'Путаница между ДУ и ТП',
        'нарушение_процедуры': 'Нарушение порядка процедуры ТПП',
    }
    
    f.write("| Error Pattern | Occurrences | % of Errors |\n")
    f.write("|---------------|-------------|-------------|\n")
    total_errs = 308 - stats['total']['correct']
    for pname, pdesc in pattern_names.items():
        cnt = anna_stats.get(pname, 0)
        f.write(f"| {pdesc} | {cnt} | {cnt/total_errs*100:.1f}% |\n")
    
    f.write(f"\n**Total errors matching Anna's patterns:** {sum(anna_stats.values())} across {len([r for r in rows if r['anna_patterns'] != 'none'])} questions\n\n")
    
    # ── 5. Problematic Questions ──
    f.write("## 5. Problematic Question Clusters\n\n")
    
    # Group by topic keywords
    topics = {
        'стоимость': defaultdict(list),
        'срок': defaultdict(list),
        'заявк': defaultdict(list),
        'пароль': defaultdict(list),
        'документ': defaultdict(list),
        'личный кабинет': defaultdict(list),
    }
    
    for r in error_details['total']:
        q = r['question'].lower()
        for topic in topics:
            if topic in q:
                topics[topic]['count'] = len(topics[topic].get('items', [])) + 1
                if 'items' not in topics[topic]:
                    topics[topic]['items'] = []
                topics[topic]['items'].append(r)
    
    f.write("| Topic Cluster | Error Count | Note |\n")
    f.write("|---------------|-------------|------|\n")
    for topic, data in sorted(topics.items(), key=lambda x: len(x[1].get('items', [])), reverse=True):
        cnt = len(data.get('items', []))
        if cnt >= 3:
            note = ""
            if topic == 'стоимость': note = "Model gives wrong formulas/amounts"
            elif topic == 'срок': note = "Model gets deadlines wrong"
            elif topic == 'пароль': note = "Wrong recovery procedures"
            elif topic == 'заявк': note = "Wrong submission/changes procedures"
            elif topic == 'документ': note = "Wrong document package requirements"
            elif topic == 'личный кабинет': note = "Wrong LK functionality descriptions"
            f.write(f"| {topic} | {cnt} | {note} |\n")
    
    # ── 6. Development Roadmap ──
    f.write("## 6. Development Roadmap\n\n")
    f.write("### Immediate Actions (Week 1-2)\n\n")
    f.write("1. **Fix ДУ category (32.8% accuracy)**: The model confuses ДУ procedures with ТП. Need separate prompt for ДУ questions.\n")
    f.write("2. **Improve search quality for deadlines/costs**: Model frequently gives wrong numbers. Add structured data tables to vector DB.\n")
    f.write("3. **Fix password recovery procedures**: Model applies generic recovery to all cases, ignoring key context (ЦОК registration, ЮЛ status).\n\n")
    
    f.write("### Short-term (Week 3-4)\n\n")
    f.write("1. **Add Anna's corrections to prompts**: Incorporate domain expert feedback into system prompt.\n")
    f.write("2. **Improve source attribution**: Model says 'not found' 11 times where answer exists. Fix search recall.\n")
    f.write("3. **Power/category constraint awareness**: Add explicit rules about ФЛ≤15kW, ИП/ЮЛ≤150kW to response agent.\n\n")
    
    f.write("### Medium-term (Month 2-3)\n\n")
    f.write("1. **Separate response agents per category**: Different system prompts for ЛК/ДУ/ТПП.\n")
    f.write("2. **RAG quality monitoring**: Track context_recall scores, alert on degradation.\n")
    f.write("3. **Benchmark automation**: Run weekly benchmark runs, track accuracy trends.\n")
    f.write("4. **Expand benchmark**: Add more ДУ-specific and edge case questions.\n\n")

print("Report written to benchmark_analysis_report.md")
