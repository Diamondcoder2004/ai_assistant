import pandas as pd
import re
import glob
import html
from pathlib import Path

def strip_html(text):
    if not isinstance(text, str): return ''
    clean = re.compile('<.*?>')
    text = re.sub(clean, '', text)
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
    text = html.unescape(text)
    return text.strip()

def parse_gift(filepath):
    qa_pairs = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    blocks = re.split(r'\n\s*\n', content)
    total_blocks = 0
    parsed = 0
    skipped = 0
    for block in blocks:
        if '// question' in block or '::' in block:
            total_blocks += 1
            question = ''
            answer = ''
            q_match = re.search(r'::.*?::(?:\[.*?\])?(.*?)\{', block, re.DOTALL)
            if q_match:
                question = strip_html(q_match.group(1))
            else:
                q_match_name = re.search(r'::(.*?)::', block, re.DOTALL)
                if q_match_name:
                    question = strip_html(q_match_name.group(1))
            options_match = re.search(r'\{(.*?)\}', block, re.DOTALL)
            if options_match:
                options = options_match.group(1)
                for line in options.split('\n'):
                    line = line.strip()
                    if line.startswith('='):
                        answer = strip_html(line[1:])
                        break
            if question and answer:
                parsed += 1
                qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})
            else:
                skipped += 1
    print(f"  [TXT] {Path(filepath).name}")
    print(f"    Всего блоков с :: или // question: {total_blocks}")
    print(f"    Успешно распарсено (есть вопрос И ответ): {parsed}")
    print(f"    Отсеяно (нет вопроса или нет ответа=): {skipped}")
    return qa_pairs

def parse_excel(filepath):
    qa_pairs = []
    try:
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.lower().str.strip()
        question_cols = ['question', 'вопрос', 'text', 'message', 'subject']
        answer_cols = ['expected_answer', 'answer', 'ответ', 'expected answer']
        q_col = next((col for col in df.columns if any(col == q for q in question_cols)), None)
        a_col = next((col for col in df.columns if any(col == a for a in answer_cols)), None)
        parsed = 0
        skipped = 0

        if q_col and a_col:
            total = len(df)
            for _, row in df.iterrows():
                question = strip_html(str(row[q_col]))
                answer = strip_html(str(row[a_col]))
                if question and answer:
                    parsed += 1
                    qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})
                else:
                    skipped += 1
            print(f"  [XLSX Q&A колонки] {Path(filepath).name}")
            print(f"    Всего строк: {total}")
            print(f"    Колонка вопросов: '{q_col}', Колонка ответов: '{a_col}'")
            print(f"    Успешно распарсено: {parsed}")
            print(f"    Отсеяно (пустые): {skipped}")

        elif 'parent' in df.columns and 'message' in df.columns and 'id' in df.columns:
            questions = df[df['parent'] == 0]
            answers = df[df['parent'] != 0]
            total_q = len(questions)
            total_a = len(answers)
            no_answer = 0
            empty_text = 0
            for _, q_row in questions.iterrows():
                q_id = q_row['id']
                question_text = strip_html(str(q_row['message']))
                if not question_text:
                    question_text = strip_html(str(q_row.get('subject', '')))
                replies = answers[answers['parent'] == q_id]
                if not replies.empty:
                    answer_text = strip_html(str(replies.iloc[0]['message']))
                    if question_text and answer_text:
                        parsed += 1
                        qa_pairs.append({'question': question_text, 'expected_answer': answer_text, 'source_file': Path(filepath).name})
                    else:
                        empty_text += 1
                else:
                    no_answer += 1
            print(f"  [XLSX форум-структура] {Path(filepath).name}")
            print(f"    Всего записей в файле: {len(df)}")
            print(f"    Записей-вопросов (parent=0): {total_q}")
            print(f"    Записей-ответов (parent!=0): {total_a}")
            print(f"    Успешно спарено (вопрос+ответ): {parsed}")
            print(f"    Отсеяно — нет ответа в таблице: {no_answer}")
            print(f"    Отсеяно — пустой текст после strip_html: {empty_text}")

        else:
            total = len(df)
            for _, row in df.iterrows():
                question = strip_html(str(row.iloc[0]))
                answer = strip_html(str(row.iloc[1]))
                if question and answer:
                    parsed += 1
                    qa_pairs.append({'question': question, 'expected_answer': answer, 'source_file': Path(filepath).name})
                else:
                    skipped += 1
            print(f"  [XLSX fallback col0+col1] {Path(filepath).name}")
            print(f"    Всего строк: {total}")
            print(f"    Успешно распарсено: {parsed}")
            print(f"    Отсеяно (пустые): {skipped}")

    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")

    return qa_pairs


print("=" * 60)
print("АНАЛИЗ ФАЙЛОВ В new_data/")
print("=" * 60)

all_qa = []
txt_files = sorted(glob.glob('d:/ai_assistant/new_data/*.txt'))
for f in txt_files:
    if 'check_excel.txt' in f:
        continue
    r = parse_gift(f)
    all_qa.extend(r)

xlsx_files = sorted(glob.glob('d:/ai_assistant/new_data/*.xlsx'))
for f in xlsx_files:
    r = parse_excel(f)
    all_qa.extend(r)

print()
print("=" * 60)
print("ИТОГОВАЯ СТАТИСТИКА")
print("=" * 60)
df = pd.DataFrame(all_qa)
print(f"Всего вопросов со всех файлов (с дублями): {len(df)}")
print()
print("Распределение по файлам-источникам:")
by_file = df.groupby('source_file').size().reset_index(name='count')
for _, row in by_file.iterrows():
    print(f"  {row['source_file']}: {row['count']} вопросов")

print()
initial = len(df)
df_unique = df.drop_duplicates(subset=['question'], keep='first')
removed = initial - len(df_unique)
print(f"Дублированных вопросов (удалено): {removed}")
print(f"УНИКАЛЬНЫХ вопросов итого: {len(df_unique)}")
print()

# Показать какой файл дублирует больше всего
print("Дубли между файлами:")
dup_mask = df.duplicated(subset=['question'], keep='first')
dups = df[dup_mask]
if len(dups) > 0:
    dup_by_file = dups.groupby('source_file').size().reset_index(name='dup_count')
    for _, row in dup_by_file.iterrows():
        print(f"  {row['source_file']}: {row['dup_count']} дублей")
else:
    print("  Дублей нет")
