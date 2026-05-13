import pandas as pd, json

# Старый CSV (100 строк)
df = pd.read_csv(r'D:\ai_assistant\api_benchmarks\benchmark_20260510_202137.csv', encoding='utf-8-sig')
row = df.iloc[0]
sj = json.loads(row['sources_json'])
print('Старый CSV, строк:', len(df))
print('Источников в первой строке:', len(sj))
for i, s in enumerate(sj):
    print(f'  [{i}] keys: {list(s.keys())}')
    print(f'      chunk_id: {s.get("chunk_id", "NONE")}')
    print(f'      id: {s.get("id", "NONE")}')

# Свежий CSV (20 строк)
df2 = pd.read_csv(r'D:\ai_assistant\api_benchmarks\benchmark_20260513_001947.csv', encoding='utf-8-sig')
row2 = df2.iloc[0]
sj2 = json.loads(row2['sources_json'])
print('\nНовый CSV, строк:', len(df2))
print('Источников в первой строке:', len(sj2))
for i, s in enumerate(sj2):
    print(f'  [{i}] keys: {list(s.keys())}')
    print(f'      chunk_id: {s.get("chunk_id", "NONE")}')
    print(f'      id: {s.get("id", "NONE")}')

# Проверяем: чанки из старого CSV — ищем любые из них в Qdrant
from tools.search_tool import SearchTool
print('\nИщем пример в Qdrant...')
tool = SearchTool()
tool.load()

# Берём первый вопрос из старого CSV
q = df.iloc[0]['question']
results = tool.search_multi(queries=[q], k=10)
if results:
    for r in results[:3]:
        cid = r.metadata.get('chunk_id', 'NONE')
        rid = r.id
        print(f'  Qdrant chunk_id: {cid}, id: {rid}')
else:
    print('  Нет результатов')
