import csv

rows = list(csv.DictReader(open('D:/ai_assistant/benchmark_review.csv', encoding='utf-8-sig')))

# Show first 20 errors with full expected/answer
errs = [r for r in rows if r['my_binary'] == '0']

with open('D:/ai_assistant/error_samples.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total errors found: {len(errs)} out of {len(rows)}\n\n")
    
    # Show first 30 errors
    for i, r in enumerate(errs[:30]):
        f.write(f"--- #{r['index']} [{r['category']}] class={r['my_class']} notes={r['notes']} ---\n")
        f.write(f"Q: {r['question'][:200]}\n")
        f.write(f"EXP: {r['expected_short']}\n")
        f.write(f"ANS: {r['answer_short']}\n\n")

print("Written error_samples.txt")
