"""
Mindmap Generator - 從 YouTube 影片逐字稿生成心智圖
使用 Gemini API 提取階層式主題結構，輸出 Mermaid mindmap 語法
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"), http_options={"api_version": "v1"})

# 快取目錄
MINDMAP_DIR = os.path.join(os.path.dirname(__file__), "..", "mindmaps")
os.makedirs(MINDMAP_DIR, exist_ok=True)

MINDMAP_PROMPT = """你是專業的心智圖設計專家，擅長將複雜內容轉化為清晰的層級結構。

## 工作流程

### 步驟一：內容分析
- 識別文件類型（報告/逐字稿/書籍）
- 確定核心主題和邊界

### 步驟二：概念提取
- 提取 5-7 個主要概念作為主分支
- 每個主分支下提取 2-5 個子項目
- 使用原文術語，保持語意準確

### 步驟三：結構建立
- 驗證層級關係（is-a / part-of）
- 確保同層符合 MECE 原則（彼此獨立、完全窮盡）

---

## 輸出要求
1. **直接輸出** Mermaid mindmap 語法，不要任何前言或解釋
2. 使用繁體中文
3. 每個節點文字簡潔，不超過 10 個字
4. 可以使用 emoji 標記主題
5. **重要：節點文字中禁止使用括號 () [] {} 和其他特殊符號，這會導致解析錯誤**

## Mermaid 語法格式
```
mindmap
  root((影片主題))
    🎯 主分支1
      子項目A
      子項目B
    📌 主分支2
      子項目C
      子項目D
```

---

## 逐字稿內容
{transcript}

請只輸出 Mermaid 語法，從 `mindmap` 開始："""


def get_cached_mindmap(video_id: str) -> str | None:
    """檢查是否有快取的心智圖"""
    cache_path = os.path.join(MINDMAP_DIR, f"{video_id}.txt")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def save_mindmap(video_id: str, mermaid_code: str) -> None:
    """儲存心智圖到快取"""
    cache_path = os.path.join(MINDMAP_DIR, f"{video_id}.txt")
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    print(f"✅ 心智圖已快取至: {cache_path}")


def get_transcript_text(video_id: str) -> str | None:
    """讀取逐字稿文字"""
    transcript_dir = os.path.join(os.path.dirname(__file__), "..", "transcripts")
    file_path = os.path.join(transcript_dir, f"{video_id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return " ".join([item.get('text', '') for item in data])
            elif isinstance(data, dict) and 'text' in data:
                return data['text']
    except Exception as e:
        print(f"⚠️ 讀取逐字稿失敗 ({video_id}): {e}")
    return None


def generate_mindmap(video_id: str, force_regenerate: bool = False) -> str | None:
    """
    生成心智圖 Mermaid 語法
    
    :param video_id: YouTube Video ID
    :param force_regenerate: 是否強制重新生成（忽略快取）
    :return: Mermaid mindmap 語法字串 or None
    """
    # 1. 檢查快取
    if not force_regenerate:
        cached = get_cached_mindmap(video_id)
        if cached:
            print(f"📦 使用快取的心智圖: {video_id}")
            return cached
    
    # 2. 讀取逐字稿
    transcript_text = get_transcript_text(video_id)
    if not transcript_text:
        print(f"❌ 找不到逐字稿: {video_id}")
        return None
    
    # 截斷過長的逐字稿
    if len(transcript_text) > 50000:
        print("⚠️ 逐字稿過長，進行截斷...")
        transcript_text = transcript_text[:50000]
    
    # 3. 使用 Gemini 生成心智圖
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ 未設定 GEMINI_API_KEY")
        return None

    print(f"🧠 正在生成心智圖: {video_id}...")

    try:
        response = _gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents="You are a content structure expert. Output ONLY Mermaid mindmap syntax, no explanation.\n\n" + MINDMAP_PROMPT.replace("{transcript}", transcript_text),
            config=types.GenerateContentConfig(temperature=0.5),
        )

        mermaid_code = response.text.strip()
        
        # 清理可能的 markdown 包裝
        if mermaid_code.startswith("```mermaid"):
            mermaid_code = mermaid_code[len("```mermaid"):].strip()
        if mermaid_code.startswith("```"):
            mermaid_code = mermaid_code[3:].strip()
        if mermaid_code.endswith("```"):
            mermaid_code = mermaid_code[:-3].strip()
        
        # 確保以 mindmap 開頭
        if not mermaid_code.startswith("mindmap"):
            print("⚠️ 生成的內容格式不正確")
            return None
        
        # 4. 儲存快取
        save_mindmap(video_id, mermaid_code)
        
        return mermaid_code
        
    except Exception as e:
        print(f"❌ 生成心智圖時發生錯誤: {e}")
        return None


def mindmap_exists(video_id: str) -> bool:
    """檢查心智圖是否已生成"""
    cache_path = os.path.join(MINDMAP_DIR, f"{video_id}.txt")
    return os.path.exists(cache_path)


# CLI 測試
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        result = generate_mindmap(video_id)
        if result:
            print("\n--- Generated Mindmap ---")
            print(result)
        else:
            print("Failed to generate mindmap")
    else:
        print("Usage: python mindmap_generator.py <video_id>")
