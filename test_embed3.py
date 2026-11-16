import httpx
import os

api_key = os.environ["GEMINI_API_KEY"]
base_url = "https://generativelanguage.googleapis.com/v1"
model = "models/text-embedding-004"

url = f"{base_url}/{model}:embedContent"
payload = {
    "model": model,
    "content": {"parts": [{"text": "test sentence for embedding"}]},
    "taskType": "RETRIEVAL_DOCUMENT",
}

response = httpx.post(url, json=payload, params={"key": api_key}, timeout=30)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    values = data.get("embedding", {}).get("values", [])
    print(f"SUCCESS: dim={len(values)}, first_3={values[:3]}")
else:
    print(f"FAIL: {response.text[:400]}")
