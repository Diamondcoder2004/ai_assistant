import pandas as pd
import difflib
import sys

# Force utf-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

old = pd.read_csv(r'D:\ai_assistant\api_benchmarks\api_benchmark_20260421_154701\results.csv', encoding='utf-8-sig')
new = pd.read_csv(r'D:\ai_assistant\backend\api_benchmarks\no_query_gen_full\benchmark_20260508_032927_judged.csv', encoding='utf-8-sig')

old.rename(columns={'judge_justification': 'judge_reasoning'}, inplace=True)
old['id'] = old['index'].astype(str)
new['id'] = new['id'].astype(str)

SEP = "=" * 90

# ==================================================
# 1. Aggregate metrics
# ==================================================
print(SEP)
print("1. AGGREGATE METRICS COMPARISON (OLD vs NEW)")
print(SEP)

METRICS = ['judge_relevance', 'judge_completeness', 'judge_helpfulness',
           'judge_clarity', 'judge_hallucination_risk', 'judge_context_recall',
           'judge_faithfulness', 'judge_currency', 'judge_overall_score']

for m in METRICS:
    old_m = old[m].mean()
    new_m = new[m].mean()
    d = new_m - old_m
    print(f"  [{('+' if d>0 else '')}{d:+.2f}] {m:<25s}: OLD={old_m:.2f}  NEW={new_m:.2f}")

for label, col in [("OLD", old['judge_binary_correctness']), ("NEW", new['judge_binary_correctness'])]:
    total = len(col)
    n1 = (col == 1).sum()
    n0 = (col == 0).sum()
    nm = (col == -1).sum()
    print(f"\n  {label}: inst_correct={n1}/{total} ({n1/total*100:.1f}%), wrong={n0} ({n0/total*100:.1f}%), unjudgeable={nm} ({nm/total*100:.1f}%)")
    if total - nm:
        print(f"  {label} accuracy (excluding unjudgeable): {n1}/{total-nm} = {n1/(total-nm)*100:.1f}%")

# ==================================================
# 2. Per-row comparison
# ==================================================
print("\n" + SEP)
print("2. PER-QUESTION BINARY COMPARISON")
print(SEP)

merged = old.merge(new, on='id', suffixes=('_old', '_new'), how='inner')
print(f"  Matched: {len(merged)}/{len(old)} questions")

old_correct = merged['judge_binary_correctness_old'] == 1
new_correct = merged['judge_binary_correctness_new'] == 1
old_not_correct = merged['judge_binary_correctness_old'] != 1
new_not_correct = merged['judge_binary_correctness_new'] != 1

both_correct = old_correct & new_correct
both_wrong = (merged['judge_binary_correctness_old'] == 0) & (merged['judge_binary_correctness_new'] == 0)
improvement = old_not_correct & new_correct
regression = old_correct & new_not_correct
old_correct_new_unable = old_correct & (merged['judge_binary_correctness_new'] == -1)

print(f"  Both correct:          {both_correct.sum():>3d}")
print(f"  Both wrong:            {both_wrong.sum():>3d}")
print(f"  [IMPROVEMENT] NEW correct, OLD not: {improvement.sum():>3d}")
print(f"  [REGRESSION]  OLD correct, NEW not: {regression.sum():>3d}")
print(f"  OLD correct, NEW unjudgeable:       {old_correct_new_unable.sum():>3d}")

# ==================================================
# 3. Improvements detail
# ==================================================
print("\n" + SEP)
print("3. IMPROVEMENTS: questions where NEW is correct but OLD was not")
print(SEP)

imp_df = merged[improvement][['id','question_old','expected_old','answer_new','answer_old',
    'judge_completeness_old','judge_completeness_new','judge_overall_score_old','judge_overall_score_new']]
imp_df.rename(columns={'expected_old': 'expected'}, inplace=True)
for _, row in imp_df.iterrows():
    q = str(row['question_old'])[:100]
    exp = str(row['expected'])[:80]
    old_ans = str(row['answer_old'])[:130].replace('\n',' ')
    new_ans = str(row['answer_new'])[:130].replace('\n',' ')
    print(f"\n  Q{row['id']}: {q}")
    print(f"  Expected: {exp}")
    print(f"  OLD (wrong):         {old_ans}")
    print(f"  NEW (correct):       {new_ans}")

# ==================================================
# 4. Regressions detail
# ==================================================
print("\n" + SEP)
print("4. REGRESSIONS: questions where OLD was correct but NEW is not")
print(SEP)

reg_df = merged[regression][['id','question_old','expected_old','answer_old','answer_new',
    'judge_completeness_old','judge_completeness_new','judge_overall_score_old','judge_overall_score_new','num_hits_old','num_hits_new']]
reg_df.rename(columns={'expected_old': 'expected'}, inplace=True)
for _, row in reg_df.iterrows():
    q = str(row['question_old'])[:100]
    exp = str(row['expected'])[:80]
    old_ans = str(row['answer_old'])[:130].replace('\n',' ')
    new_ans = str(row['answer_new'])[:130].replace('\n',' ')
    print(f"\n  Q{row['id']}: {q}")
    print(f"  Expected: {exp}")
    print(f"  OLD (correct):       {old_ans}")
    print(f"  NEW (wrong):         {new_ans}")

# ==================================================
# 5. Answer similarity distribution
# ==================================================
print("\n" + SEP)
print("5. ANSWER SIMILARITY DISTRIBUTION")
print(SEP)

def sim(a, b):
    a = str(a)[:200].strip().lower()
    b = str(b)[:200].strip().lower()
    return difflib.SequenceMatcher(None, a, b).ratio()

merged['answer_similarity'] = merged.apply(lambda r: sim(r['answer_old'], r['answer_new']), axis=1)
avg_sim = merged['answer_similarity'].mean()
print(f"  Average answer similarity (first 200 chars): {avg_sim:.1%}")
print(f"  Very similar (>80%):  {(merged['answer_similarity']>0.8).sum():>3d}/{len(merged)}")
print(f"  Quite different (<40%): {(merged['answer_similarity']<0.4).sum():>3d}/{len(merged)}")

# ==================================================
# 6. Domain category analysis
# ==================================================
print("\n" + SEP)
print("6. ANALYSIS BY DOMAIN CATEGORY")
print(SEP)

def classify(q):
    if not isinstance(q, str): return 'other'
    ql = q.lower()
    if any(w in ql for w in ['личн','лк','кабинет','парол','регистрац','менеджер','email','e-mail','логин']):
        return 'LK'
    if any(w in ql for w in ['дополнительн','ду ','услуг','услуги']):
        return 'DU'
    if any(w in ql for w in ['тп ','тпп','технологическ','присоединен','ту ','заявк','мощност',
           'договор','сетев','электр','подключен','срок','акт','выполнен','оплат','присоед']):
        return 'TPP'
    return 'other'

merged['category'] = merged['question_old'].apply(classify)
for cat, grp in merged.groupby('category'):
    n = len(grp)
    old_c = (grp['judge_binary_correctness_old'] == 1).sum()
    new_c = (grp['judge_binary_correctness_new'] == 1).sum()
    impr = ((grp['judge_binary_correctness_old'] != 1) & (grp['judge_binary_correctness_new'] == 1)).sum()
    regr = ((grp['judge_binary_correctness_old'] == 1) & (grp['judge_binary_correctness_new'] != 1)).sum()
    print(f"\n  {cat:<10s} ({n} questions):")
    print(f"    OLD correct: {old_c:>3d}/{n} ({old_c/n*100:.0f}%)")
    print(f"    NEW correct: {new_c:>3d}/{n} ({new_c/n*100:.0f}%)")
    if impr + regr:
        print(f"    Improvements: {impr:>3d}  |  Regressions: {regr:>3d}")

# ==================================================
# 7. New questions analysis
# ==================================================
print("\n" + SEP)
print("7. NEW ANSWERS ANALYSIS")
print(SEP)

# Check average confidence on correct vs wrong
new_c = new[new['judge_binary_correctness'] == 1]
new_w = new[new['judge_binary_correctness'] == 0]
print(f"  NEW correct: avg confidence={new_c['confidence'].mean():.2f}, avg hits={new_c['num_hits'].mean():.1f}")
print(f"  NEW wrong:   avg confidence={new_w['confidence'].mean():.2f}, avg hits={new_w['num_hits'].mean():.1f}")

print("\n" + SEP)
print("SUMMARY")
print(SEP)
print(f"  Old baseline (with QueryGen):    {old['judge_binary_correctness'].value_counts().get(1,0)}/308 correct ({old['judge_binary_correctness'].value_counts().get(1,0)/308*100:.1f}%)")
print(f"  New system (no QueryGen):         {new['judge_binary_correctness'].value_counts().get(1,0)}/308 correct ({new['judge_binary_correctness'].value_counts().get(1,0)/308*100:.1f}%)")
print(f"  Improvements: {improvement.sum()}  |  Regressions: {regression.sum()}")
print(f"  Overall binary improvement:       +{new['judge_binary_correctness'].value_counts().get(1,0)-old['judge_binary_correctness'].value_counts().get(1,0)} correct")
print(SEP)
