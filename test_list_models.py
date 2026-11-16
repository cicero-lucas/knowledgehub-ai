import httpx
import os

api_key = os.environ["GEMINI_API_KEY"]

for version in ["v1", "v1beta"]:
    url = f"https://generativelanguage.googleapis.com/{version}/models"
    resp = httpx.get(url, params={"key": api_key}, timeout=30)
    if resp.status_code != 200:
        print(f"{version}: ERROR {resp.status_code}")
        continue
    models = resp.json().get("models", [])
    embed_models = [
        m["name"]
        for m in models
        if "embedContent" in m.get("supportedGenerationMethods", [])
    ]
    print(f"\n=== {version} EMBEDDING MODELS ({len(embed_models)}) ===")
    for m in embed_models:
        print(f"  {m}")
    if not embed_models:
        print("  (none available)")
