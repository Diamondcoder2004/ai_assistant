import pandas as pd
import re
import glob
from pathlib import Path
import html

def strip_html(text):
    if not isinstance(text, str):
        return ""
    # Remove HTML tags
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    # Replace common HTML entities
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
    # Unescape
    text = html.unescape(text)
    return text.strip()

def parse_gift(filepath):
    qa_pairs = []
    for enc in ('utf-8-sig', 'utf-16', 'cp1251', 'utf-8'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        print(f"Could not decode {filepath}")
        return qa_pairs

    # Moodle GIFT format block split
    blocks = re.split(r'\n\s*\n', content)
    for block in blocks:
        if '// question' in block or '::' in block:
            question = ""
            answer = ""

            # extract question text (after second :: and before {)
            q_match = re.search(r'::.*?::(?:\[.*?\])?(.*?)\{', block, re.DOTALL)
            if q_match:
                question = strip_html(q_match.group(1))
            else:
                # fall back to name if text not found between :: and {
                q_match_name = re.search(r'::(.*?)::', block, re.DOTALL)
                if q_match_name:
                    question = strip_html(q_match_name.group(1))
                else:
                    continue

            # extract correct answer (starts with =)
            options_match = re.search(r'\{(.*?)\}', block, re.DOTALL)
            if options_match:
                options = options_match.group(1)
                for line in options.split('\n'):
                    line = line.strip()
                    if line.startswith('='):
                        answer = strip_html(line[1:])
                        break
            if question and answer:
                qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})
    return qa_pairs

def parse_excel(filepath):
    qa_pairs = []
    try:
        df = pd.read_excel(filepath)

        # Normalize column names to lowercase for easier matching
        df.columns = df.columns.str.lower().str.strip()

        # Приоритет 1: subject (вопрос) + message (ответ с HTML)
        if 'subject' in df.columns and 'message' in df.columns:
            print(f"Parsing {Path(filepath).name} via subject+message ({len(df)} rows)")
            for _, row in df.iterrows():
                question = str(row['subject']).strip()
                answer = strip_html(str(row['message']))
                if question and answer:
                    qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})

        # Приоритет 2: стандартные Q&A колонки (вопрос/ответ или question/answer)
        else:
            question_cols = ['question', 'вопрос', 'text']
            answer_cols = ['expected_answer', 'answer', 'ответ', 'expected answer']
            q_col = next((col for col in df.columns if col in question_cols), None)
            a_col = next((col for col in df.columns if col in answer_cols), None)

            if q_col and a_col:
                print(f"Parsing {Path(filepath).name} via {q_col}+{a_col} ({len(df)} rows)")
                for _, row in df.iterrows():
                    question = strip_html(str(row[q_col]))
                    answer = strip_html(str(row[a_col]))
                    if question and answer:
                        qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})
            else:
                # Fallback: первая колонка = вопрос, вторая = ответ
                if len(df.columns) >= 2:
                    print(f"Parsing {Path(filepath).name} via col[0]+col[1] fallback ({len(df)} rows)")
                    for _, row in df.iterrows():
                        question = strip_html(str(row.iloc[0]))
                        answer = strip_html(str(row.iloc[1]))
                        if question and answer:
                            qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})

        print(f"  -> Извлечено пар: {len(qa_pairs)}")

    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return qa_pairs

all_qa = []
txt_files = glob.glob('d:/ai_assistant/new_data/*.txt')
for f in txt_files:
    if 'check_excel.txt' in f: continue
    if 'analysis_output.txt' in f: continue
    all_qa.extend(parse_gift(f))

xlsx_files = glob.glob('d:/ai_assistant/new_data/*.xlsx')
for f in xlsx_files:
    all_qa.extend(parse_excel(f))

df_out = pd.DataFrame(all_qa)
if not df_out.empty:
    initial_len = len(df_out)
    df_out = df_out.drop_duplicates(subset=['question'], keep='first')
    print(f"Removed {initial_len - len(df_out)} duplicate questions.")

output_path = 'd:/ai_assistant/new_data/benchmark_dataset.csv'
df_out.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"Total unique QA pairs: {len(df_out)}")
print(f"Saved to: {output_path}")
