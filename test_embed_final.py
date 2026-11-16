import httpx, os

api_key = os.environ["GEMINI_API_KEY"]

for model in ["models/gemini-embedding-001", "models/gemini-embedding-2"]:
    url = f"https://generativelanguage.googleapis.com/v1/{model}:embedContent"
    payload = {
        "model": model,
        "content": {"parts": [{"text": "test sentence"}]},
        "taskType": "RETRIEVAL_DOCUMENT",
    }
    resp = httpx.post(url, json=payload, params={"key": api_key}, timeout=30)
    if resp.status_code == 200:
        values = resp.json()["embedding"]["values"]
        print(f"SUCCESS {model}: dim={len(values)}")
    else:
        print(f"FAIL    {model}: {resp.text[:200]}")
