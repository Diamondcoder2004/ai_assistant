import pandas as pd
import requests
import json
import os
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("ROUTERAI_BASE_URL", "https://routerai.ru/api/v1") + "/chat/completions"
API_KEY = os.getenv("ROUTERAI_API_KEY")
MODEL = os.getenv("DEFAULT_LLM_MODEL", "inception/mercury-2")

benchmark_dir = r"d:\ai_assistant\api_benchmarks\api_benchmark_20260419_200723"
input_csv = os.path.join(benchmark_dir, "results.csv")
output_csv = os.path.join(benchmark_dir, "antigravity_eval_results.csv")

PROMPT_TEMPLATE = """Ты - Antigravity, мощный ИИ-ассистент. Твоя задача - строго и справедливо оценить ответ системы на заданный вопрос по 5-балльной шкале. 

Вопрос: {question}
Ожидаемый ответ: {expected}
Фактический ответ системы: {answer}

Оцени ответ по 5-балльной шкале (1 - ужасно, 5 - идеально), учитывая точность, полноту и отсутствие галлюцинаций.
Верни ТОЛЬКО ОДНУ ЦИФРУ от 1 до 5 (например, "4" или "5"). Никаких других слов."""

def evaluate_row(row_data):
    index, question, expected, answer = row_data
    prompt = PROMPT_TEMPLATE.format(question=question, expected=expected, answer=answer)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 5
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        score_text = data['choices'][0]['message']['content'].strip()
        # extract first digit
        digits = ''.join(filter(str.isdigit, score_text))
        score = float(digits[:1]) if digits else 0.0
        return index, score
    except Exception as e:
        print(f"Error on {index}: {e}")
        return index, 0.0

def main():
    print("Reading CSV...")
    df = pd.read_csv(input_csv, encoding='utf-8')
    print(f"Total rows: {len(df)}. Evaluating with Antigravity prompt via RouterAI using ThreadPoolExecutor...")
    
    rows = [(row['index'], row['question'], row['expected'], row['answer']) for _, row in df.iterrows()]
    
    eval_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_idx = {executor.submit(evaluate_row, r): r[0] for r in rows}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_idx)):
            idx, score = future.result()
            eval_dict[idx] = score
            if (i+1) % 50 == 0:
                print(f"Evaluated {i+1}/{len(rows)}")
    
    df['antigravity_score'] = df['index'].map(eval_dict)
    
    df_out = df[['index', 'question', 'expected', 'answer', 'antigravity_score']]
    df_out.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Done. Saved to {output_csv}")
    print("Antigravity Average Score:", df_out['antigravity_score'].mean())

if __name__ == "__main__":
    main()
