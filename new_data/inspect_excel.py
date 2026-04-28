import pandas as pd
import glob
from pathlib import Path

xlsx_files = sorted(glob.glob('d:/ai_assistant/new_data/*.xlsx'))
for f in xlsx_files:
    df = pd.read_excel(f)
    print(f"\n{'='*60}")
    print(f"FILE: {Path(f).name}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\n--- Первые 3 строки (subject + message) ---")
    for i, row in df.head(3).iterrows():
        print(f"\n  Row {i}:")
        if 'subject' in df.columns:
            print(f"  SUBJECT: {repr(str(row['subject'])[:200])}")
        if 'message' in df.columns:
            print(f"  MESSAGE: {repr(str(row['message'])[:300])}")
    print(f"\n--- Пустые значения ---")
    for col in ['subject', 'message']:
        if col in df.columns:
            nulls = df[col].isna().sum()
            empty = (df[col].astype(str).str.strip() == '').sum()
            print(f"  {col}: NaN={nulls}, empty_str={empty}, total_rows={len(df)}")
