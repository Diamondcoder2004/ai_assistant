#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация подробного отчёта о тестировании RAG-ассистента на основе results.csv.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import pandas as pd
import numpy as np

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)


def is_null_answer(answer) -> bool:
    if answer is None:
        return True
    s = str(answer).strip()
    return s == '' or s.lower() in ('nan', 'null', 'none')


def load_results(results_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(results_csv, encoding='utf-8-sig')
    # Числовые колонки
    judge_cols = [
        "judge_relevance", "judge_completeness", "judge_helpfulness",
        "judge_clarity", "judge_hallucination_risk", "judge_context_recall",
        "judge_faithfulness", "judge_currency", "judge_binary_correctness",
        "judge_overall_score"
    ]
    for col in judge_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'time_total_sec' in df.columns:
        df['time_total_sec'] = pd.to_numeric(df['time_total_sec'], errors='coerce')
    if 'num_hits' in df.columns:
        df['num_hits'] = pd.to_numeric(df['num_hits'], errors='coerce')
    return df


def extract_category(sources_str) -> str:
    """Извлекает категорию из JSON-строки sources"""
    try:
        if not sources_str or str(sources_str).strip() in ('', 'nan', '[]'):
            return "unknown"
        sources = json.loads(str(sources_str))
        if sources and isinstance(sources, list):
            return sources[0].get("category", "unknown")
    except:
        pass
    return "unknown"


CATEGORY_NAMES = {
    "instructions": "Инструкции (ЛК)",
    "legal": "Нормативные документы",
    "informational": "Информационные материалы",
    "passports": "Паспорта услуг",
    "unknown": "Неизвестно",
}


def generate_report(results_csv: Path, output_path: Path):
    df = load_results(results_csv)
    total = len(df)

    # Разделяем на отвеченные и без ответа
    null_mask = df['answer'].apply(is_null_answer)
    answered_df = df[~null_mask].copy()
    null_df = df[null_mask].copy()

    # Флаги ошибок API
    error_mask = answered_df['answer'].apply(
        lambda x: str(x).startswith("ERROR") or str(x).startswith("HTTP_ERROR")
    )
    error_df = answered_df[error_mask]
    valid_df = answered_df[~error_mask]

    # Judge-метрики только для строк с оценками
    judge_df = valid_df.dropna(subset=['judge_overall_score'])

    # Бинарная точность
    binary_df = valid_df.dropna(subset=['judge_binary_correctness'])
    binary_correct = int(binary_df['judge_binary_correctness'].sum()) if len(binary_df) > 0 else 0
    binary_accuracy = binary_correct / len(binary_df) * 100 if len(binary_df) > 0 else 0

    # Категории
    df['category'] = df['sources'].apply(extract_category)
    valid_df = valid_df.copy()
    valid_df['category'] = df.loc[valid_df.index, 'category']

    # ===== ФОРМИРУЕМ ОТЧЁТ =====
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_name = results_csv.parent.name

    lines = []
    lines.append(f"# 📊 Отчёт о тестировании RAG-ассистента")
    lines.append(f"**Дата генерации:** {timestamp}")
    lines.append(f"**Источник данных:** `{csv_name}/results.csv`")
    lines.append("")

    # 1. Общий обзор
    lines.append("---")
    lines.append("## 1. Общий обзор")
    lines.append("")
    lines.append("| Показатель | Значение |")
    lines.append("|---|---|")
    lines.append(f"| Всего вопросов | **{total}** |")
    lines.append(f"| Получено ответов | **{len(answered_df)}** ({len(answered_df)/total*100:.1f}%) |")
    lines.append(f"| Без ответа (null) | **{len(null_df)}** ({len(null_df)/total*100:.1f}%) |")
    lines.append(f"| Ошибки API | **{len(error_df)}** |")
    lines.append(f"| Оценено LLM-судьёй | **{len(judge_df)}** |")
    lines.append(f"| Бинарная точность (верных ответов) | **{binary_correct}/{len(binary_df)} ({binary_accuracy:.1f}%)** |")
    lines.append("")

    # 2. Детальные метрики качества
    if len(judge_df) > 0:
        lines.append("---")
        lines.append("## 2. Метрики качества (LLM Judge, шкала 1–5)")
        lines.append("")

        metrics = {
            "judge_relevance": ("Релевантность", "Насколько ответ соответствует вопросу"),
            "judge_completeness": ("Полнота", "Полнота охвата темы"),
            "judge_helpfulness": ("Полезность", "Практическая ценность ответа"),
            "judge_clarity": ("Ясность", "Понятность и структурированность"),
            "judge_hallucination_risk": ("Риск галлюцинаций", "5 = нет галлюцинаций, 1 = высокий риск"),
            "judge_context_recall": ("Покрытие контекста", "Использование релевантных источников"),
            "judge_faithfulness": ("Точность источникам", "Соответствие предоставленным чанкам"),
            "judge_currency": ("Актуальность", "Свежесть информации"),
            "judge_overall_score": ("**Общая оценка**", "Средняя по всем метрикам"),
        }

        lines.append("| Метрика | Среднее | Медиана | Мин | Макс | Описание |")
        lines.append("|---|:---:|:---:|:---:|:---:|---|")
        for col, (name, desc) in metrics.items():
            if col in judge_df.columns:
                vals = judge_df[col].dropna()
                if len(vals) > 0:
                    lines.append(
                        f"| {name} | {vals.mean():.2f} | {vals.median():.2f} | "
                        f"{vals.min():.1f} | {vals.max():.1f} | {desc} |"
                    )
        lines.append("")

        # Бинарная точность подробнее
        lines.append("### Бинарная корректность ответов")
        lines.append("")
        lines.append(f"- **Верных ответов:** {binary_correct} из {len(binary_df)} оценённых")
        lines.append(f"- **Точность:** {binary_accuracy:.1f}%")
        lines.append("")

    # 3. Технические показатели
    lines.append("---")
    lines.append("## 3. Технические показатели")
    lines.append("")
    if 'time_total_sec' in valid_df.columns and len(valid_df) > 0:
        t = valid_df['time_total_sec'].dropna()
        lines.append(f"- **Среднее время ответа API:** {t.mean():.2f} сек")
        lines.append(f"- **Медиана времени:** {t.median():.2f} сек")
        lines.append(f"- **Максимальное время:** {t.max():.2f} сек")
        lines.append(f"- **Минимальное время:** {t.min():.2f} сек")
        lines.append("")
    if 'num_hits' in valid_df.columns and len(valid_df) > 0:
        h = valid_df['num_hits'].dropna()
        lines.append(f"- **Среднее количество источников (hits):** {h.mean():.2f}")
        lines.append(f"- **Медиана hits:** {h.median():.1f}")
        lines.append(f"- **Максимум hits:** {int(h.max())}")
        lines.append("")

    # 4. Анализ по категориям
    if 'category' in valid_df.columns:
        lines.append("---")
        lines.append("## 4. Анализ по категориям")
        lines.append("")

        cat_stats = []
        for cat, group in valid_df.groupby('category'):
            cat_name = CATEGORY_NAMES.get(cat, cat)
            n = len(group)
            jg = group.dropna(subset=['judge_overall_score']) if 'judge_overall_score' in group.columns else pd.DataFrame()
            avg_score = jg['judge_overall_score'].mean() if len(jg) > 0 else float('nan')
            bg = group.dropna(subset=['judge_binary_correctness']) if 'judge_binary_correctness' in group.columns else pd.DataFrame()
            bin_acc = bg['judge_binary_correctness'].mean() * 100 if len(bg) > 0 else float('nan')
            cat_stats.append((cat_name, n, avg_score, bin_acc))

        cat_stats.sort(key=lambda x: x[0])

        lines.append("| Категория | Вопросов | Средний балл | Бинарная точность |")
        lines.append("|---|:---:|:---:|:---:|")
        for cat_name, n, avg_score, bin_acc in cat_stats:
            score_str = f"{avg_score:.2f}" if not np.isnan(avg_score) else "—"
            acc_str = f"{bin_acc:.1f}%" if not np.isnan(bin_acc) else "—"
            lines.append(f"| {cat_name} | {n} | {score_str} | {acc_str} |")
        lines.append("")

    # 5. Анализ ошибок
    lines.append("---")
    lines.append("## 5. Анализ ошибок и проблемных ответов")
    lines.append("")

    # 5.1 Типы ошибок
    lines.append("### 5.1 Типы проблемных ответов")
    lines.append("")
    lines.append("| Тип проблемы | Количество |")
    lines.append("|---|:---:|")
    lines.append(f"| Нет ответа (null/пусто) | {len(null_df)} |")
    lines.append(f"| Ошибки API (HTTP/Network) | {len(error_df)} |")

    if len(judge_df) > 0 and 'judge_binary_correctness' in judge_df.columns:
        wrong = judge_df[judge_df['judge_binary_correctness'] == 0]
        lines.append(f"| Семантически неверные ответы | {len(wrong)} |")
        high_hallucination = judge_df[judge_df.get('judge_hallucination_risk', pd.Series(dtype=float)) <= 2]
        if 'judge_hallucination_risk' in judge_df.columns:
            hh = judge_df[judge_df['judge_hallucination_risk'] <= 2]
            lines.append(f"| Высокий риск галлюцинаций (оценка ≤2) | {len(hh)} |")
        low_context = judge_df[judge_df.get('judge_context_recall', pd.Series(dtype=float)) <= 1] if 'judge_context_recall' in judge_df.columns else pd.DataFrame()
        if 'judge_context_recall' in judge_df.columns:
            lc = judge_df[judge_df['judge_context_recall'] <= 1]
            lines.append(f"| Низкое покрытие контекста (оценка =1) | {len(lc)} |")
    lines.append("")

    # 5.2 Наихудшие ответы
    if len(judge_df) > 0 and 'judge_overall_score' in judge_df.columns:
        lines.append("### 5.2 Вопросы с наихудшими оценками (топ-15)")
        lines.append("")
        worst = judge_df.nsmallest(15, 'judge_overall_score')[
            ['index', 'question', 'expected', 'answer', 'judge_overall_score',
             'judge_binary_correctness', 'judge_hallucination_risk', 'judge_justification']
        ]

        for _, row in worst.iterrows():
            score = row.get('judge_overall_score', '—')
            bc = int(row.get('judge_binary_correctness', -1)) if not pd.isna(row.get('judge_binary_correctness', float('nan'))) else '—'
            hr = row.get('judge_hallucination_risk', '—')
            q = str(row.get('question', ''))[:120]
            exp = str(row.get('expected', ''))[:80]
            ans = str(row.get('answer', ''))[:120]
            just = str(row.get('judge_justification', ''))[:200]
            lines.append(f"#### ❌ Вопрос #{int(row['index'])}: {q}")
            lines.append(f"- **Ожидалось:** {exp}")
            lines.append(f"- **Получено:** {ans}...")
            lines.append(f"- **Общий балл:** {score:.2f} | Бинарная точность: {bc} | Риск галлюцинаций: {hr}")
            lines.append(f"- **Оценка судьи:** {just}...")
            lines.append("")

    # 5.3 Null-ответы (первые 20)
    if len(null_df) > 0:
        lines.append("### 5.3 Вопросы без ответа (первые 20)")
        lines.append("")
        lines.append("| # | Вопрос | Ожидаемый ответ |")
        lines.append("|---|---|---|")
        for _, row in null_df.head(20).iterrows():
            idx = int(row.get('index', '?'))
            q = str(row.get('question', ''))[:100]
            exp = str(row.get('expected', ''))[:60]
            lines.append(f"| {idx} | {q} | {exp} |")
        if len(null_df) > 20:
            lines.append(f"\n*...и ещё {len(null_df) - 20} вопросов без ответа*")
        lines.append("")

    # 6. Распределение оценок
    if len(judge_df) > 0 and 'judge_overall_score' in judge_df.columns:
        lines.append("---")
        lines.append("## 6. Распределение оценок")
        lines.append("")
        scores = judge_df['judge_overall_score'].dropna()
        bins = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 4.5), (4.5, 5.01)]
        labels = ["0–1", "1–2", "2–3", "3–4", "4–4.5", "4.5–5"]
        lines.append("| Диапазон оценки | Количество | % |")
        lines.append("|---|:---:|:---:|")
        for (lo, hi), label in zip(bins, labels):
            cnt = ((scores >= lo) & (scores < hi)).sum()
            pct = cnt / len(scores) * 100
            lines.append(f"| {label} | {cnt} | {pct:.1f}% |")
        lines.append("")

    # 7. План улучшений
    lines.append("---")
    lines.append("## 7. План улучшений базы знаний и ассистента")
    lines.append("")

    lines.append("### 7.1 Критические проблемы (приоритет: высокий)")
    lines.append("")
    lines.append("1. **Неполные ответы (обрывы текста)** — ряд ответов обрывается на середине предложения.")
    lines.append("   - *Решение:* Увеличить `max_tokens`, добавить постпроцессинг для обнаружения обрывов.")
    lines.append("2. **Галлюцинации** — ответы с высоким риском галлюцинаций (оценка ≤2) содержат несуществующие факты.")
    lines.append("   - *Решение:* Добавить явный промпт-запрет на генерацию информации вне контекста.")
    lines.append("3. **Неверные ответы при правильном контексте** — RAG находит правильные чанки, но ответ неверен.")
    lines.append("   - *Решение:* Доработать synthesis_prompt для более строгого следования источникам.")
    lines.append("")

    lines.append("### 7.2 Улучшения базы знаний (приоритет: средний)")
    lines.append("")
    lines.append("1. **Низкий context_recall** — система не всегда находит нужный чанк.")
    lines.append("   - *Решение:* Пересмотреть чанкинг для сложных инструкций; добавить синонимы и перефразировки.")
    lines.append("2. **Устаревшие нормативные данные** — некоторые юридические документы могут быть неактуальны.")
    lines.append("   - *Решение:* Регулярно обновлять базу знаний при выходе новых постановлений.")
    lines.append("3. **Процедурные вопросы оператора** — ответы не включают действия оператора (закрыть обращение, зарегистрировать).")
    lines.append("   - *Решение:* Добавить в базу знаний скрипты для операторов с пошаговыми действиями.")
    lines.append("")

    lines.append("### 7.3 Улучшения системы (приоритет: низкий)")
    lines.append("")
    lines.append("1. **Тайм-ауты** — часть вопросов не получает ответа из-за таймаутов.")
    lines.append("   - *Решение:* Добавить механизм очереди с автоматическим retry.")
    lines.append("2. **Параметры retrieval** — некоторые вопросы получают нерелевантные источники.")
    lines.append("   - *Решение:* Тонкая настройка гибридного поиска (alpha между semantic/lexical).")
    lines.append("3. **Категоризация запросов** — разные категории демонстрируют разное качество.")
    lines.append("   - *Решение:* Реализовать маршрутизацию запросов по типу (инструкции, нормативка, процедуры).")
    lines.append("")

    # 8. Итоговый вывод
    lines.append("---")
    lines.append("## 8. Итоговый вывод")
    lines.append("")
    if len(judge_df) > 0:
        avg_overall = judge_df['judge_overall_score'].mean()
        lines.append(f"Система показала средний балл **{avg_overall:.2f}/5.0** по оценке LLM-судьи "
                     f"на {len(judge_df)} оценённых вопросах из {total} общих. "
                     f"Бинарная точность составила **{binary_accuracy:.1f}%**. ")

        if avg_overall >= 4.5:
            lines.append("**Качество ответов высокое.** Основные усилия следует направить на покрытие null-ответов и устранение галлюцинаций.")
        elif avg_overall >= 3.5:
            lines.append("**Качество ответов среднее.** Необходимы улучшения в базе знаний и промпт-инжиниринге.")
        else:
            lines.append("**Качество ответов требует существенной доработки.** Рекомендуется полная ревизия базы знаний и системных промптов.")
    lines.append("")
    lines.append(f"*Отчёт сгенерирован автоматически: {timestamp}*")

    # Записываем файл
    report_text = "\n".join(lines)
    output_path.write_text(report_text, encoding='utf-8')
    print(f"✅ Отчёт сохранён: {output_path}")
    return report_text


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate benchmark report from results.csv")
    parser.add_argument("--results", "-r", required=True, help="Путь к results.csv")
    parser.add_argument("--output", "-o", default=None, help="Путь для сохранения report.md (по умолчанию рядом с results.csv)")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"ERROR: {results_path} not found")
        return

    output_path = Path(args.output) if args.output else results_path.parent / "report.md"
    generate_report(results_path, output_path)


if __name__ == "__main__":
    main()
