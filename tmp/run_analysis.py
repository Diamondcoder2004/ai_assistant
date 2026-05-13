import sys, logging
sys.argv = ["analyze_components", "D:/ai_assistant/backend/api_benchmarks/benchmark_20260513_075934_enriched.csv"]

# Redirect stdout/stderr to file
import io
import os
os.makedirs("D:/ai_assistant/tmp", exist_ok=True)
sys.stdout = io.TextIOWrapper(open(sys.__stdout__.buffer.fileno(), 'wb', buffering=0), encoding='utf-8', errors='replace')
sys.stderr = sys.stdout

exec(open("D:/ai_assistant/backend/analyze_components.py", encoding='utf-8').read())
