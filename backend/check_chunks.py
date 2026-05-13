import json, os, sys
sys.path.insert(0, '.')
import config as cfg

chunks_dir = 'chunking/enriched_chunks'
for cat in ['normative', 'operational']:
    d = os.path.join(chunks_dir, cat)
    files = [f for f in os.listdir(d) if f.endswith('.json')]
    print(f'Category {cat}: {len(files)} files')
    if files:
        with open(os.path.join(d, files[0]), 'r', encoding='utf-8') as fh:
            ch = json.load(fh)
        src_origin = ch.get('source_origin', 'MISSING')
        src_file = ch.get('source_file', 'MISSING')
        coll = cfg.NORMATIVE_COLLECTION_NAME if src_origin == 'normative' else cfg.OPERATIONAL_COLLECTION_NAME
        print(f'  source_origin: {src_origin}')
        print(f'  source_file: {src_file}')
        print(f'  collection_name would be: {coll}')
    
    # Check content length of contextual text
    if files:
        with open(os.path.join(d, files[1]), 'r', encoding='utf-8') as fh:
            ch1 = json.load(fh)
        content_len = len(ch1.get('chunk_content',ch1.get('content','')))
        print(f'  sample content length: {content_len}')

# Also show current env vars
print()
print(f'cfg.NORMATIVE_COLLECTION_NAME = {cfg.NORMATIVE_COLLECTION_NAME}')
print(f'cfg.OPERATIONAL_COLLECTION_NAME = {cfg.OPERATIONAL_COLLECTION_NAME}')
