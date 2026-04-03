import os
from google import genai

def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("未設定 GEMINI_API_KEY")
    return genai.Client(api_key=api_key, http_options={"api_version": "v1"})
