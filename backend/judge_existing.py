"""Run LLM Judge on an existing benchmark CSV (no re-retrieval)."""
import csv
import json
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import JUDGE_LLM_MODEL
from llm_judge import LLMJudge, LLMEvaluation


def run_judge_on_csv(input_csv: str, output_dir: str):
    """Read existing benchmark CSV, run judge on each row, write new CSV."""
    input_path = Path(input_csv)
    if not input_path.exists():
        logger.error(f"Input CSV not found: {input_csv}")
        return

    output_path = Path(output_dir) / input_path.name.replace(".csv", "_judged.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Read all rows
    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    judge = LLMJudge()
    logger.info(f"Judge initialized: model={JUDGE_LLM_MODEL}")
    logger.info(f"Loaded {len(rows)} samples from {input_csv}")

    # Add judge columns if not present
    judge_cols = [
        "judge_relevance", "judge_completeness", "judge_helpfulness",
        "judge_clarity", "judge_hallucination_risk", "judge_context_recall",
        "judge_faithfulness", "judge_currency", "judge_binary_correctness",
        "judge_overall_score", "judge_justification",
    ]
    for col in judge_cols:
        if col not in fieldnames:
            fieldnames.append(col)

    judged = 0
    correct = 0

    for i, row in enumerate(rows):
        question = row.get("question", "")
        answer = row.get("answer", "")
        expected = row.get("expected", "")
        source_file = row.get("source_file", "")

        if not answer or answer.startswith("ERROR:"):
            logger.warning(f"[{i+1}/{len(rows)}] Skipping (no answer/error)")
            continue

        # Parse sources
        try:
            sources_raw = json.loads(row.get("sources_json", "[]"))
        except json.JSONDecodeError:
            sources_raw = []

        source_info = []
        for src in sources_raw:
            if isinstance(src, dict):
                source_info.append({
                    "chunk_id": src.get("chunk_id", ""),
                    "filename": src.get("filename", ""),
                    "content": src.get("content", ""),
                    "summary": src.get("summary", ""),
                    "breadcrumbs": src.get("breadcrumbs", ""),
                    "category": src.get("category", ""),
                    "score_hybrid": src.get("score_hybrid", 0.0),
                })

        try:
            llm_eval: LLMEvaluation = judge.evaluate(
                question=question,
                answer=answer,
                sources=source_info,
                expected=expected,
            )
            row["judge_relevance"] = str(llm_eval.relevance)
            row["judge_completeness"] = str(llm_eval.completeness)
            row["judge_helpfulness"] = str(llm_eval.helpfulness)
            row["judge_clarity"] = str(llm_eval.clarity)
            row["judge_hallucination_risk"] = str(llm_eval.hallucination_risk)
            row["judge_context_recall"] = str(llm_eval.context_recall)
            row["judge_faithfulness"] = str(llm_eval.faithfulness)
            row["judge_currency"] = str(llm_eval.currency)
            row["judge_binary_correctness"] = str(llm_eval.binary_correctness)
            row["judge_overall_score"] = str(round(llm_eval.overall_score, 2))
            row["judge_justification"] = (llm_eval.reasoning or "")[:500]
            judged += 1
            if llm_eval.binary_correctness == 1:
                correct += 1
            pct = (correct / judged * 100) if judged > 0 else 0
            logger.info(
                f"[{i+1}/{len(rows)}] binary={llm_eval.binary_correctness} "
                f"overall={llm_eval.overall_score:.1f} "
                f"({correct}/{judged} = {pct:.1f}%)"
            )
        except Exception as e:
            logger.error(f"[{i+1}/{len(rows)}] Judge error: {e}")
            row["judge_binary_correctness"] = "-1"
            row["judge_justification"] = f"ERROR: {str(e)[:500]}"

        # Save incrementally every 10 rows
        if (i + 1) % 10 == 0:
            with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

    # Final save
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"\n{'='*60}")
    logger.info(f"JUDGE COMPLETE: {correct}/{judged} = {correct/judged*100:.1f}% binary correct")
    logger.info(f"Output: {output_path}")
    logger.info(f"{'='*60}")

    # Save stats
    stats_path = output_path.parent / output_path.name.replace(".csv", "_stats.json")
    stats = {
        "judge_model": JUDGE_LLM_MODEL,
        "judge_evaluated": judged,
        "judge_binary_correct": correct,
        "judge_binary_rate": f"{correct/judged*100:.1f}%" if judged > 0 else "N/A",
    }
    if judged > 0:
        for col in ["relevance", "completeness", "helpfulness", "clarity", "hallucination_risk", "context_recall", "faithfulness", "currency", "overall_score"]:
            vals = [float(r[f"judge_{col}"]) for r in rows if r.get(f"judge_{col}", "") and r[f"judge_{col}"].replace(".","").replace("-","").isdigit()]
            if vals:
                stats[f"judge_avg_{col}"] = round(sum(vals) / len(vals), 2)

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run LLM Judge on existing benchmark CSV")
    parser.add_argument("--input", required=True, help="Path to benchmark CSV")
    parser.add_argument("--output", default="api_benchmarks", help="Output directory")
    args = parser.parse_args()

    stats = run_judge_on_csv(args.input, args.output)
    if stats:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
