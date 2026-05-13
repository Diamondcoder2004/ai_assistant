"""Identify worst-performing benchmark cases using actual CSV structure."""
import pandas as pd
import json

df = pd.read_csv("backend/api_benchmarks/benchmark_20260507_003759.csv", encoding="utf-8-sig")

# Map unnamed columns to their actual content (they have header values as data)
# From inspection: C9=time_total_sec, C10=num_hits, C12=confidence,
# C13=judge_relevance, C14=judge_completeness, C15=judge_helpfulness,
# C16=judge_clarity, C17=judge_hallucination_risk, C18=judge_context_recall,
# C19=judge_faithfulness, C20=judge_currency

# Read with proper column mapping - first check if header exists
# The issue is header got mixed with data. Let's use column indices.
cols_map = {
    "id": "id",
    "question": "question",
    "expected": "expected",
    "answer": "answer",
    "judge_binary_correctness": "judge_binary_correctness",
    "judge_reasoning": "judge_reasoning",
    "judge_overall_score": "judge_overall_score",
    "C9": "time_total_sec",
    "C10": "num_hits",
    "C12": "confidence",
    "C13": "judge_relevance",
    "C14": "judge_completeness",
    "C15": "judge_helpfulness",
    "C16": "judge_clarity",
    "C17": "judge_hallucination_risk",
    "C18": "judge_context_recall",
    "C19": "judge_faithfulness",
    "C20": "judge_currency",
    "queries": "queries",
}

# Rename columns
df = df.rename(columns={k: v for k, v in cols_map.items() if k in df.columns})

# Convert score columns to numeric
score_cols = ["judge_relevance", "judge_completeness", "judge_helpfulness",
              "judge_clarity", "judge_hallucination_risk", "judge_context_recall",
              "judge_faithfulness", "judge_currency", "judge_overall_score",
              "judge_binary_correctness", "num_hits", "confidence"]
for c in score_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

print(f"Total rows: {len(df)}")
print(f"Rows with valid judge_overall_score (>0): {(df['judge_overall_score'] > 0).sum()}")

# Filter valid judge evaluations
valid = df[df["judge_overall_score"] > 0].copy()
print(f"Valid evaluations: {len(valid)}")

if len(valid) == 0:
    # Try without filter - maybe header row issue
    # Check if first row is actually headers
    print("\nWARNING: No valid rows with judge_overall_score > 0")
    print("First row values:")
    for c in df.columns[:15]:
        print(f"  {c}: {df.iloc[0][c]}")
    exit()

# --- CORE ANALYSIS ---

# Category 1: Binary=0 AND relevance<=2
binary0 = valid[valid["judge_binary_correctness"] == 0]
print(f"\nBinary=0 cases: {len(binary0)}")
print(f"  Avg relevance: {binary0['judge_relevance'].mean():.2f}")
print(f"  Avg context_recall: {binary0['judge_context_recall'].mean():.2f}")
print(f"  Avg completeness: {binary0['judge_completeness'].mean():.2f}")
print(f"  Avg hits: {binary0['num_hits'].mean():.1f}")

# Binary=1 comparison
binary1 = valid[valid["judge_binary_correctness"] == 1]
print(f"\nBinary=1 cases: {len(binary1)}")
print(f"  Avg relevance: {binary1['judge_relevance'].mean():.2f}")
print(f"  Avg context_recall: {binary1['judge_context_recall'].mean():.2f}")
print(f"  Avg completeness: {binary1['judge_completeness'].mean():.2f}")
print(f"  Avg hits: {binary1['num_hits'].mean():.1f}")

# Delta analysis
print(f"\n{'='*70}")
print("DELTA: Binary=1 minus Binary=0")
print("=" * 70)
metrics = [
    ("judge_relevance", "Relevance"),
    ("judge_completeness", "Completeness"),
    ("judge_context_recall", "Context Recall"),
    ("judge_faithfulness", "Faithfulness"),
    ("judge_hallucination_risk", "Hallucination Risk"),
    ("num_hits", "Sources Retrieved"),
]
for col, name in metrics:
    d = binary1[col].mean() - binary0[col].mean()
    print(f"  {name:22s}: delta={d:+.2f}  (1={binary1[col].mean():.2f}, 0={binary0[col].mean():.2f})")

# Find worst of worst: binary=0, relevance<=2, context_recall<=2
cat_worst = valid[(valid["judge_binary_correctness"] == 0) & 
                   (valid["judge_relevance"] <= 2) & 
                   (valid["judge_context_recall"] <= 2)]
print(f"\n{'='*70}")
print(f"WORST OF WORST (binary=0, relevance<=2, context_recall<=2): {len(cat_worst)}")
print("=" * 70)

# Show top 20 worst cases sorted by overall score
worst = cat_worst.nsmallest(20, "judge_overall_score")
for _, row in worst.iterrows():
    print(f"\n--- Q#{int(row['id'])} (overall={row['judge_overall_score']:.2f}, hits={int(row['num_hits'])}) ---")
    print(f"  Relevance: {row['judge_relevance']} | Completeness: {row['judge_completeness']} | ContextRecall: {row['judge_context_recall']}")
    print(f"  Faithfulness: {row['judge_faithfulness']} | HallucinationRisk: {row['judge_hallucination_risk']}")
    q = str(row['question'])[:250]
    print(f"  Q: {q}")
    ans = str(row.get('answer', ''))[:300]
    print(f"  Answer: {ans}")

# --- PATTERN ANALYSIS ---
print(f"\n{'='*70}")
print("PATTERN ANALYSIS")
print("=" * 70)

# 1. Question categories that fail
print("\n1. Question topics among worst cases:")
# Simple keyword analysis
keywords = ["стоимост", "расчет", "тариф", "цена", "оплат", "счет", "рассрочк", "льгот",
           "заявк", "подат", "документ", "форма",
           "срок", "период", "длительн",
           "мощност", "кВт", "напряжен", "категор",
           "ЛК", "личный кабинет", "кабинет",
           "СНТ", "садовод",
           "восстановить", "восстановлен", "дубликат", "переоформ",
           "расторгнут", "расторжен",
           "ДУ", "дополнительн", "услуг",
           "акт", "ТП", "подписан",
           "ИП", "ЮЛ", "ФЛ",
           "изменен", "увеличен"]

keyword_hits = {}
for kw in keywords:
    cnt = cat_worst['question'].str.contains(kw, case=False, na=False).sum()
    if cnt > 0:
        keyword_hits[kw] = cnt

for kw, cnt in sorted(keyword_hits.items(), key=lambda x: -x[1]):
    print(f"  '{kw}': {cnt}/{len(cat_worst)} questions ({cnt/len(cat_worst)*100:.0f}%)")

# 2. Source count distribution for failures
print(f"\n2. Source count distribution in worst cases:")
for n in range(11):
    cnt = (cat_worst['num_hits'] == n).sum()
    if cnt > 0:
        print(f"  {n} sources: {cnt} cases")

# 3. Average scores by source count
print(f"\n3. Avg scores by source count (all valid):")
for n in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
    subset = valid[valid['num_hits'] == n]
    if len(subset) >= 3:
        print(f"  {n} sources ({len(subset)} cases): relevance={subset['judge_relevance'].mean():.2f}, binary_rate={subset['judge_binary_correctness'].mean()*100:.0f}%")

print("\nDone.")
