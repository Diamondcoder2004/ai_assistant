import pandas as pd, json
df = pd.read_csv('D:/ai_assistant/api_benchmarks/benchmark_20260513_075934.csv', encoding='utf-8-sig')
print('Rows:', len(df))
print('Cols:', list(df.columns))

def get_prefix(sj):
    try:
        s = json.loads(sj)
        if s:
            cid = s[0].get('chunk_id','')
            return cid.split('_p')[0] if '_p' in cid else cid[:12]
    except: pass
    return 'N/A'

for i in range(min(5, len(df))):
    print(f'Row {i}: prefix={get_prefix(df.iloc[i]["sources_json"])}')
