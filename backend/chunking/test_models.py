#!/usr/bin/env python3
"""Quick test: which models support JSON mode via RouterAI."""

import asyncio
from openai import AsyncOpenAI

API_KEY = "sk-5ArynRNUi11lFMyvtj5NBv4bFPS0xBs0"
BASE_URL = "https://routerai.ru/api/v1"

MODELS = [
    'openai/gpt-4o-mini',
    'meta-llama/llama-4-maverick',
    'qwen/qwen3.5-flash-02-23',
    'qwen/qwen3.5-02-23',
    'deepseek/deepseek-chat',
    'deepseek/deepseek-v3',
]


async def test_model(client, model):
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{
                'role': 'user',
                'content': 'Return JSON with a single key "test" and value "ok". Only the JSON, no other text.'
            }],
            max_tokens=100,
            temperature=0,
            response_format={'type': 'json_object'}
        )
        content = response.choices[0].message.content
        print(f'  {model}: OK -> {content[:100]}')
        return True
    except Exception as e:
        print(f'  {model}: FAIL -> {type(e).__name__}: {str(e)[:150]}')
        return False


async def main():
    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=30)
    
    print("Testing JSON mode support:\n")
    results = {}
    for model in MODELS:
        ok = await test_model(client, model)
        results[model] = ok
    
    print("\n=== SUMMARY ===")
    for model, ok in results.items():
        status = "SUPPORTS JSON MODE" if ok else "NO JSON MODE"
        print(f"  {model}: {status}")


if __name__ == '__main__':
    asyncio.run(main())
