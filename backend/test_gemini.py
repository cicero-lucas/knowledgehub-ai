"""
Run: python test_gemini.py
Tests Gemini API key, embedding model, and generation model.
"""
import os
from dotenv import load_dotenv

load_dotenv(".env")

API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
GEN_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-1.5-flash")

print(f"API_KEY   : {API_KEY[:10]}..." if API_KEY else "API_KEY   : NOT SET")
print(f"EMBED_MODEL: {EMBED_MODEL}")
print(f"GEN_MODEL  : {GEN_MODEL}\n")

# ── 1. List available models ──────────────────────────────────────────────────
import google.generativeai as genai
genai.configure(api_key=API_KEY)

print("=== Available models ===")
for m in genai.list_models():
    if "embed" in m.name.lower() or "flash" in m.name.lower() or "pro" in m.name.lower():
        print(f"  {m.name}  |  {m.supported_generation_methods}")

# ── 2. Test embedding ─────────────────────────────────────────────────────────
import httpx
print(f"\n=== Testing embedding: {EMBED_MODEL} ===")
url = f"https://generativelanguage.googleapis.com/v1/{EMBED_MODEL}:embedContent"
payload = {"model": EMBED_MODEL, "content": {"parts": [{"text": "hello world"}]}, "taskType": "RETRIEVAL_DOCUMENT"}
r = httpx.post(url, json=payload, params={"key": API_KEY}, timeout=30)
if r.status_code == 200:
    vec = r.json().get("embedding", {}).get("values", [])
    print(f"  OK — dimension: {len(vec)}")
else:
    print(f"  FAILED {r.status_code}: {r.text[:300]}")

# ── 3. Test generation ────────────────────────────────────────────────────────
print(f"\n=== Testing generation: {GEN_MODEL} ===")
try:
    model = genai.GenerativeModel(model_name=GEN_MODEL)
    resp = model.generate_content("Say 'OK' and nothing else.")
    print(f"  OK — response: {resp.text.strip()}")
except Exception as e:
    print(f"  FAILED: {e}")
