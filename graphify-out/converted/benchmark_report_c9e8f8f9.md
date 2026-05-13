<!-- converted from benchmark_report.docx -->


Benchmark Analysis Report
AI Assistant (Башкирэнерго)

308 questions evaluated | 39.0% correct | Judge agreement 92.9%
Date: 2026-04-28
Review method: Judge LLM (deepseek-v3.2) + manual semantic verification

# Table of Contents

# 1. Executive Summary
This report presents the results of benchmarking the AI Assistant for Bashkirenergo's technical connection support. 308 questions across three domain categories were evaluated using a judge LLM (deepseek-v3.2) supplemented by manual semantic verification.

Key metrics:
• Total questions: 308
• Correct answers: 120 (39.0%)
• Errors: 188 (61.0%)
• Judge-model agreement: 286/308 (92.9%)
• Answer not found in sources: 11 cases
• Average judge overall score: 3.71 / 10

## 1.1 Category Breakdown


The worst-performing category is ДУ (Additional Services) at 32.8% accuracy. The model frequently confuses ДУ procedures with ТП procedures, leading to incorrect recommendations.
ЛК (Personal Account) performs best at 54.7%, suggesting the model has better grounding in the most common customer questions.

# 2. Error Pattern Analysis
Classification of errors according to Anna Borisovna's review notes from expert evaluation:
## 2.1 Error Pattern Distribution


Key observations:
• Terminology errors are the most common — model uses incorrect business vocabulary like "обычный заявитель" (should be ФЛ/ИП/ЮЛ) and "сетевой орган" (should be сетевая организация)
• Cost calculation errors affect 22.9% of all errors — model provides wrong amounts, formulas, or tariff rates
• Power/constraint errors (21.8%) — model fails to distinguish between ФЛ ≤ 15 kW, ИП/ЮЛ ≤ 150 kW, and свыше 150 kW categories

# 3. Judge LLM Objectivity Analysis
The benchmark uses deepseek-v3.2 as a judge model to evaluate answer quality across 10 criteria.


The judge LLM demonstrates high reliability (92.9% agreement). No cases of leniency were found — the judge never passed an incorrect answer as correct. All 5 disagreement cases were the judge being too strict, penalizing verbose-but-substantively-correct answers.

Verdict: The judge model is fit for purpose. It can be used for automated benchmark evaluation with high confidence.

# 4. Development Roadmap
## 4.1 Immediate Actions (Week 1-2)
1. Fix ДУ category accuracy (currently 32.8%)
The model confuses ДУ (Additional Services) procedures with ТП (Technical Connection). Create separate system prompt for ДУ questions with explicit procedural boundaries.
2. Improve search quality for deadlines and costs
Model frequently gives wrong numerical answers. Add structured data tables to the vector database for cost amounts, deadlines, and tariff rates.
3. Fix password recovery procedures
Model applies generic password recovery to all cases, ignoring critical context differences (ЦОК registration, ЮЛ status, first-time vs returning user).
## 4.2 Short-term (Week 3-4)
1. Incorporate Anna Borisovna's expert corrections into system prompts
2. Improve source attribution — model says answer not found 11 times where it exists in sources
3. Add explicit power/category constraint rules to response agent (ФЛ ≤ 15 kW, ИП/ЮЛ ≤ 150 kW)
## 4.3 Medium-term (Month 2-3)
1. Separate response agents per domain category (ЛК / ДУ / ТПП)
2. Implement RAG quality monitoring — track context_recall scores, alert on degradation
3. Automate weekly benchmark runs with accuracy trend tracking
4. Expand benchmark dataset with more ДУ-specific and edge case questions
5. Reduce terminology errors through domain-specific fine-tuning or constrained vocabulary
| Category | Questions | Correct | % Correct | Avg Score |
| --- | --- | --- | --- | --- |
| Личный кабинет (ЛК) | 53 | 29 | 54.7% | 4.17 |
| Дополнительные услуги (ДУ) | 67 | 22 | 32.8% | 3.51 |
| Технологическое присоединение (ТПП) | 188 | 69 | 36.7% | 3.65 |
| ВСЕГО | 308 | 120 | 39.0% | 3.71 |
| Error Pattern | Occurrences | % of Errors |
| --- | --- | --- |
| Неверная терминология ("обычный заявитель", "сетевой орган") | 69 | 36.7% |
| Неверный расчёт стоимости или тарифы | 43 | 22.9% |
| Не учтены ограничения по мощности / категории заявителя | 41 | 21.8% |
| Льготная ставка / соц.льгота применяется некорректно | 22 | 11.7% |
| Путаница между ДУ и ТП | 6 | 3.2% |
| Metric | Value |
| --- | --- |
| Total questions evaluated | 308 |
| Judge agrees with manual review | 286 (92.9%) |
| Judge too strict (correct → wrong) | 5 (1.6%) |
| Judge too lenient (wrong → correct) | 0 (0%) |
| No judge data available | 17 (5.5%) |