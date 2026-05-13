import csv

# Step 1: Read the previous benchmark results to get worst question IDs
previous_results = {}
with open(r'D:\ai_assistant\backend\api_benchmarks\benchmark_20260507_003759.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        q = row.get('question', '')
        s = row.get('judge_overall_score', '').strip()
        if q and s and s not in ('judge_overall_score', '', 'None'):
            try:
                score = float(s)
                if score < 0:  # Bad scores
                    previous_results[q] = score
            except:
                pass

# Step 2: Sort and get worst 10 unique questions
sorted_worst = sorted(previous_results.items(), key=lambda x: x[1])
worst_questions = [q for q, _ in sorted_worst[:10]]

print(f"Found {len(worst_questions)} worst questions from previous run:")
for i, (q, s) in enumerate(sorted_worst[:10]):
    print(f"  {i+1}. [{s}] {q[:80]}")

# Step 3: Look them up in full benchmark dataset
full_rows = {}
with open(r'D:\ai_assistant\new_data\benchmark_dataset.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        full_rows[row['question']] = row

# Step 4: Write mini CSV
found = 0
with open(r'D:\ai_assistant\backend\worst10_questions.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['question', 'expected_answer', 'source_file'])
    for q in worst_questions:
        row = full_rows.get(q)
        if row:
            writer.writerow([q, row.get('expected_answer', ''), row.get('source_file', '')])
            found += 1
        else:
            print(f"  NOT FOUND in benchmark dataset: {q[:80]}")

print(f"\nWrote {found}/{len(worst_questions)} questions to worst10_questions.csv")
