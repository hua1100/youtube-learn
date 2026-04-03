import os
from google import genai

_client: genai.Client | None = None

def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("未設定 GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key, http_options={"api_version": "v1"})
    return _client
