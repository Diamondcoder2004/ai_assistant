"""
analyze_components.py — анализ вклада компонентов поиска через Ridge регрессию.

Читает enriched CSV с колонками cited_pref, cited_hype, cited_bm25, cited_contextual, cited_count
и обучает Ridge (L2) регрессию для 4 целевых переменных:
  - judge_binary_correctness -> бинарная (1/0), классификация
  - judge_relevance          -> 1-5, регрессия
  - judge_context_recall     -> 0-1, регрессия
  - judge_overall_score      -> 1-5, регрессия

Для binary_correctness использует LogisticRegression с L2 penalty.
Для остальных — Ridge (LinearRegression с L2).

Вывод: таблица коэффициентов для каждой модели + важность фич.

Запуск:
    cd backend
    python analyze_components.py ../api_benchmarks/benchmark_20260510_202137_enriched.csv

Зависимости: pandas, numpy, scikit-learn (добавить при необходимости)
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import (
    r2_score, mean_squared_error, accuracy_score,
    roc_auc_score, classification_report
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("analyze")


# Целевые переменные и их тип
TARGETS = {
    "judge_binary_correctness": "binary",
    "judge_relevance": "regression",
    "judge_context_recall": "regression",
    "judge_overall_score": "regression",
}

# Признаки
FEATURES = ["cited_pref", "cited_hype", "cited_bm25", "cited_contextual"]


def load_enriched_csv(input_csv: str) -> pd.DataFrame:
    """Загружает enriched CSV и проверяет наличие необходимых колонок."""
    logger.info(f"Загружаем: {input_csv}")
    df = pd.read_csv(input_csv, encoding="utf-8-sig")
    logger.info(f"Строк: {len(df)}, колонок: {list(df.columns)}")

    missing_features = [f for f in FEATURES if f not in df.columns]
    if missing_features:
        logger.error(f"Нет признаков: {missing_features}")
        sys.exit(1)

    missing_targets = [t for t in TARGETS if t not in df.columns]
    if missing_targets:
        logger.warning(f"Нет целевых переменных: {missing_targets} — работаем с теми что есть")

    available_targets = {k: v for k, v in TARGETS.items() if k in df.columns}
    return df, available_targets


def filter_valid_data(df: pd.DataFrame, feature_cols: list, target_col: str) -> pd.DataFrame:
    """Фильтрует строки с валидными данными: не-NaN, не-ERROR, cited_count > 0."""
    valid = df.copy()

    # Убираем строки с ошибками
    if "answer" in valid.columns:
        valid = valid[~valid["answer"].str.contains("ERROR", na=False)]

    # Убираем строки с NaN в фичах или таргете
    valid = valid.dropna(subset=feature_cols + [target_col])

    # Убираем sentinel -1 ("not evaluated") из таргета
    valid = valid[valid[target_col] != -1]

    # Убираем строки где нет совпадений по поиску
    if "cited_count" in valid.columns:
        valid = valid[valid["cited_count"] > 0]

    # Убираем строки где все фичи нулевые
    valid = valid[~(valid[feature_cols] == 0.0).all(axis=1)]

    return valid


def train_ridge_model(
    X: np.ndarray, y: np.ndarray,
    feature_names: list, target_name: str
) -> dict:
    """
    Обучает Ridge регрессию с cross-validation.
    Возвращает коэффициенты, метрики, CV scores.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Подбор alpha через CV
    alphas = [0.01, 0.1, 1.0, 10.0, 100.0]
    best_score = -np.inf
    best_alpha = 1.0
    best_model = None

    for alpha in alphas:
        model = Ridge(alpha=alpha, random_state=42)
        scores = cross_val_score(model, X_scaled, y, cv=5,
                                 scoring="r2" if len(np.unique(y)) > 2 else "neg_mean_squared_error")
        mean_score = scores.mean()
        if mean_score > best_score:
            best_score = mean_score
            best_alpha = alpha

    # Финальная модель с лучшим alpha
    final_model = Ridge(alpha=best_alpha, random_state=42)
    final_model.fit(X_scaled, y)
    y_pred = final_model.predict(X_scaled)

    # CV метрики
    cv_r2 = cross_val_score(final_model, X_scaled, y, cv=5, scoring="r2")
    cv_mse = cross_val_score(final_model, X_scaled, y, cv=5, scoring="neg_mean_squared_error")

    # Важность фич по стандартизированным коэффициентам
    coef_series = pd.Series(final_model.coef_, index=feature_names)
    importance = coef_series.abs().sort_values(ascending=False)

    return {
        "target": target_name,
        "type": "ridge",
        "best_alpha": best_alpha,
        "n_samples": len(y),
        "coefs": coef_series.to_dict(),
        "importance": importance.to_dict(),
        "r2_train": round(r2_score(y, y_pred), 3),
        "mse_train": round(mean_squared_error(y, y_pred), 3),
        "cv_r2_mean": round(cv_r2.mean(), 3),
        "cv_r2_std": round(cv_r2.std(), 3),
        "cv_mse_mean": round(-cv_mse.mean(), 3),
    }


def train_logistic_model(
    X: np.ndarray, y: np.ndarray,
    feature_names: list, target_name: str
) -> dict:
    """
    Обучает LogisticRegression с L2 penalty для бинарной классификации.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Подбор C (обратный alpha) через CV
    C_values = [0.01, 0.1, 1.0, 10.0, 100.0]
    best_score = -np.inf
    best_C = 1.0
    best_model = None

    for C in C_values:
        model = LogisticRegression(l1_ratio=0, C=C, solver="liblinear", random_state=42, max_iter=1000)
        scores = cross_val_score(model, X_scaled, y, cv=5, scoring="roc_auc")
        mean_score = scores.mean()
        if mean_score > best_score:
            best_score = mean_score
            best_C = C

    # Финальная модель
    final_model = LogisticRegression(l1_ratio=0, C=best_C, solver="liblinear", random_state=42, max_iter=1000)
    final_model.fit(X_scaled, y)
    y_pred = final_model.predict(X_scaled)
    y_proba = final_model.predict_proba(X_scaled)[:, 1]

    # CV метрики
    cv_auc = cross_val_score(final_model, X_scaled, y, cv=5, scoring="roc_auc")
    cv_acc = cross_val_score(final_model, X_scaled, y, cv=5, scoring="accuracy")

    # Коэффициенты
    coef_series = pd.Series(final_model.coef_[0], index=feature_names)
    importance = coef_series.abs().sort_values(ascending=False)

    return {
        "target": target_name,
        "type": "logistic",
        "best_C": best_C,
        "n_samples": len(y),
        "class_balance": f"{y.sum()}/{len(y) - y.sum()} (1/0)",
        "coefs": coef_series.to_dict(),
        "importance": importance.to_dict(),
        "accuracy_train": round(accuracy_score(y, y_pred), 3),
        "auc_train": round(roc_auc_score(y, y_pred), 3),
        "cv_auc_mean": round(cv_auc.mean(), 3),
        "cv_auc_std": round(cv_auc.std(), 3),
        "cv_acc_mean": round(cv_acc.mean(), 3),
    }


def run_analysis(input_csv: str) -> None:
    """Основной цикл: для каждой целевой переменной — обучение + вывод."""
    df, available_targets = load_enriched_csv(input_csv)

    if not available_targets:
        logger.error("Нет ни одной целевой переменной для анализа.")
        sys.exit(1)

    logger.info(f"Доступные таргеты: {list(available_targets.keys())}")
    logger.info(f"Признаки: {FEATURES}")

    results = []

    for target, task_type in available_targets.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Таргет: {target} (тип: {task_type})")
        logger.info(f"{'='*60}")

        valid_df = filter_valid_data(df, FEATURES, target)
        n_before = len(df)
        n_after = len(valid_df)
        logger.info(f"Отфильтровано: {n_before} -> {n_after} строк "
                    f"(отброшено {n_before - n_after})")

        if n_after < 5:
            logger.warning(f"Слишком мало данных ({n_after}) для обучения. Пропускаем.")
            continue

        X = valid_df[FEATURES].values
        y = valid_df[target].values

        # Дескриптивная статистика
        logger.info(f"  Распределение таргета: "
                    f"mean={y.mean():.3f}, std={y.std():.3f}, "
                    f"min={y.min():.3f}, max={y.max():.3f}")

        logger.info(f"  Средние значения признаков:")
        for feat in FEATURES:
            mean_val = valid_df[feat].mean()
            std_val = valid_df[feat].std()
            logger.info(f"    {feat}: mean={mean_val:.3f}, std={std_val:.3f}")

        if task_type == "binary":
            result = train_logistic_model(X, y, FEATURES, target)
        else:
            result = train_ridge_model(X, y, FEATURES, target)

        results.append(result)

        # Вывод результатов
        logger.info(f"\n  --- Результаты для {target} ---")
        logger.info(f"  Тип: {result['type']}")
        logger.info(f"  N: {result['n_samples']}")
        if task_type == "binary":
            logger.info(f"  Лучший C: {result['best_C']}")
            logger.info(f"  Class balance: {result['class_balance']}")
            logger.info(f"  Accuracy (train): {result['accuracy_train']}")
            logger.info(f"  AUC (train): {result['auc_train']}")
            logger.info(f"  CV AUC: {result['cv_auc_mean']} ± {result['cv_auc_std']}")
            logger.info(f"  CV Accuracy: {result['cv_acc_mean']}")
        else:
            logger.info(f"  Лучший alpha: {result['best_alpha']}")
            logger.info(f"  R2 (train): {result['r2_train']}")
            logger.info(f"  MSE (train): {result['mse_train']}")
            logger.info(f"  CV R2: {result['cv_r2_mean']} ± {result['cv_r2_std']}")

        logger.info(f"\n  Коэффициенты (стандартизированные):")
        for feat, coef in sorted(result["coefs"].items(), key=lambda x: abs(x[1]), reverse=True):
            logger.info(f"    {feat:25s}: {coef:+.4f}")

        logger.info(f"\n  Важность фич (|coef|):")
        for feat, imp in result["importance"].items():
            logger.info(f"    {feat:25s}: {imp:.4f}")

    # Сводная таблица
    if results:
        logger.info(f"\n\n{'='*60}")
        logger.info("СВОДНАЯ ТАБЛИЦА КОЭФФИЦИЕНТОВ")
        logger.info(f"{'='*60}")
        header = f"{'Таргет':30s} | {'pref':>8s} | {'hype':>8s} | {'bm25':>8s} | {'contextual':>8s}"
        logger.info(header)
        logger.info("-" * len(header))
        for r in results:
            c = r["coefs"]
            line = (f"{r['target']:30s} | {c.get('cited_pref', 0):+8.4f} | "
                    f"{c.get('cited_hype', 0):+8.4f} | {c.get('cited_bm25', 0):+8.4f} | "
                    f"{c.get('cited_contextual', 0):+8.4f}")
            logger.info(line)
        logger.info("-" * len(header))

        # Какая фича чаще всего самая важная
        logger.info(f"\n\nСамая важная фича по каждому таргету:")
        for r in results:
            top_feat = list(r["importance"].keys())[0]
            logger.info(f"  {r['target']:30s} -> {top_feat} ({r['importance'][top_feat]:.4f})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python analyze_components.py <enriched_benchmark.csv>")
        print("  Ожидает CSV с колонками cited_pref, cited_hype, cited_bm25, cited_contextual")
        sys.exit(1)

    run_analysis(sys.argv[1])
