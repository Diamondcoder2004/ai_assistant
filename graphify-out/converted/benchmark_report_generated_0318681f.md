<!-- converted from benchmark_report_generated.docx -->

Benchmark Analysis Report
AI Assistant (Башкирэнерго)


# 1. Executive Summary

## Category Breakdown

# 2. Detailed Statistics by Category
## 2.1. Личный кабинет (ЛК)
Total: 53 questions | Correct: 29 (54.7%) | Errors: 24 (45.3%)

## 2.2. Дополнительные услуги (ДУ)
Total: 67 questions | Correct: 22 (32.8%) | Errors: 45 (67.2%)

## 2.3. Технологическое присоединение (ТПП)
Total: 188 questions | Correct: 69 (36.7%) | Errors: 119 (63.3%)

# 3. Judge LLM Objectivity Analysis
The judge model (deepseek-v3.2) achieved 286/308 (92.9%) agreement with manual semantic review.

## Disagreements (5 cases):
- #43 ДУ: Judge=0, Manual=1, Judge says wrong but justification positive
- #91 ДУ: Judge=0, Manual=1, Judge says wrong but justification positive
- #94 ДУ: Judge=0, Manual=1, Judge says wrong but justification positive
- #99 ДУ: Judge=0, Manual=1, Judge says wrong but justification positive
- #111 ТПП: Judge=0, Manual=1, Judge says wrong but justification positive

## Judge bias analysis:
Judge was too strict: 5
Judge was too lenient: 0
No judge data available: 17

Bias verdict: Judge tends to be overly strict

# 4. Error Patterns (Anna Borisovna)

Total errors matching patterns: 181 across 115 questions

# 5. Development Roadmap
## Immediate Actions (Week 1-2)
- Fix ДУ category (32.8% accuracy): Model confuses ДУ procedures with ТП. Need separate prompt for ДУ questions.
- Improve search quality for deadlines/costs: Model frequently gives wrong numbers. Add structured data tables to vector DB.
- Fix password recovery procedures: Model applies generic recovery to all cases, ignoring key context.

## Short-term (Week 3-4)
- Add Anna corrections to prompts: Incorporate domain expert feedback into system prompt.
- Improve source attribution: Model says 'not found' 11 times where answer exists. Fix search recall.
- Power/category constraint awareness: Add explicit rules about ФЛ≤15kW, ИП/ЮЛ≤150kW.

## Medium-term (Month 2-3)
- Separate response agents per category: Different system prompts for ЛК/ДУ/ТПП.
- RAG quality monitoring: Track context_recall scores, alert on degradation.
- Benchmark automation: Run weekly benchmark runs, track accuracy trends.
- Expand benchmark: Add more ДУ-specific and edge case questions.
| Date: | 2026-04-28 |
| --- | --- |
| Dataset: | combined_benchmark.csv (308 questions) |
| Review method: | Judge LLM (deepseek-v3.2) + manual semantic verification |
|  |  |
| Total questions: | 308 |
| --- | --- |
| Correct answers: | 120 (39.0%) |
| Errors: | 188 (61.0%) |
| Judge-model agreement: | 286/308 (92.9%) |
| Answer not found: | 11 cases |
| Average judge overall_score: | 3.71 |
| Category | Questions | Correct | % | Avg Score |
| --- | --- | --- | --- | --- |
| Личный кабинет | 53 | 29 | 54.7% | 4.17 |
| Дополнительные услуги | 67 | 22 | 32.8% | 3.51 |
| Технологическое присоединение | 188 | 69 | 36.7% | 3.65 |
| Всего | 308 | 120 | 39.0% | 3.71 |
| Classification | Count | % |
| --- | --- | --- |
| Exact match | 17 | 32.1% |
| Meaning correct | 12 | 22.6% |
| Error | 21 | 39.6% |
| Not found | 3 | 5.7% |
| Classification | Count | % |
| --- | --- | --- |
| Exact match | 9 | 13.4% |
| Meaning correct | 13 | 19.4% |
| Error | 45 | 67.2% |
| Classification | Count | % |
| --- | --- | --- |
| Exact match | 38 | 20.2% |
| Meaning correct | 31 | 16.5% |
| Error | 111 | 59.0% |
| Not found | 8 | 4.3% |
| Error Pattern | Occurrences | % of Errors |
| --- | --- | --- |
| Incorrect terminology | 69 | 36.7% |
| Power/category limitations not considered | 41 | 21.8% |
| Incorrect cost calculation or tariffs | 43 | 22.9% |
| Social benefit rate applied incorrectly | 22 | 11.7% |
| Confusion between ДУ and ТП | 6 | 3.2% |
| TPP procedure order violation | 0 | 0.0% |