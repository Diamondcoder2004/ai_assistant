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
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
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
        if 'parent' not in df.columns or 'message' not in df.columns or 'id' not in df.columns:
            return qa_pairs
            
        questions = df[df['parent'] == 0]
        answers = df[df['parent'] != 0]
        
        for _, q_row in questions.iterrows():
            q_id = q_row['id']
            question_text = strip_html(q_row['message'])
            if not question_text:
                question_text = strip_html(q_row['subject'])
            
            replies = answers[answers['parent'] == q_id]
            if not replies.empty:
                answer_text = strip_html(replies.iloc[0]['message'])
                if question_text and answer_text:
                    qa_pairs.append({'question': question_text, 'expected_answer': answer_text, 'source_file': Path(filepath).name})
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return qa_pairs

all_qa = []
txt_files = glob.glob('d:/ai_assistant/new_data/*.txt')
for f in txt_files:
    if 'check_excel.txt' in f: continue
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
