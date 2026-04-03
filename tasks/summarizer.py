import os
import json
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

_gemini_key = os.getenv("GEMINI_API_KEY")
if _gemini_key:
    genai.configure(api_key=_gemini_key)

PROMPT_TEMPLATE = """
你是一個專業的影片內容分析助手。請「直接」輸出 Markdown 格式的內容摘要，**嚴禁包含任何前言、結論、確認語句或開場白**（例如：「好的」、「以下是我的分析」、「我將為您...」等）。

### ⚠️ 重要指令 (CRITICAL INSTRUCTIONS):
1. **直接輸出**：你的輸出必須直接從 `## 內容摘要` 開始。任何在 `## 內容摘要` 之前的文字都是不允許的。
2. **僅限逐字稿內容**：你提供的所有資訊必須「完全且唯一」來自下方提供的逐字稿內容。
3. **禁止範例干擾**：範例僅供「格式參考」，嚴禁引用範例中的任何具體資訊。

### 輸出結構：
## 內容摘要
[深入摘要內容]

## 主要問題
[清單]

## 有條理的內容整理
**[類別]**
* [細節]

## 精煉亮點
[行動指引]

---
逐字稿內容如下：
{transcript}
"""


def get_transcript_text(video_id, save_to_file=False):
    """
    獲取逐字稿文字（透過 Supadata API）。
    :param video_id: YouTube Video ID
    :param save_to_file: 是否儲存為 JSON 檔案 (transcripts/{video_id}.json)
    :return: 逐字稿純文字 string or None
    """
    # 1. 檢查本地快取
    transcript_dir = os.path.join(os.path.dirname(__file__), "..", "transcripts")
    os.makedirs(transcript_dir, exist_ok=True)
    file_path = os.path.join(transcript_dir, f"{video_id}.json")

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return " ".join([item.get('text', '') for item in data])
                elif isinstance(data, dict) and 'text' in data:
                    return data['text']
        except Exception as e:
            print(f"⚠️ 讀取本地逐字稿失敗 ({video_id}): {e}")

    # 2. 透過 Supadata API 獲取逐字稿
    api_key = os.getenv("SUPADATA_API_KEY")
    if not api_key:
        print("❌ 未設定 SUPADATA_API_KEY，無法獲取逐字稿。")
        return None

    try:
        resp = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            params={"videoId": video_id},
            headers={"x-api-key": api_key},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        content = data.get("content", [])
        if not content:
            print(f"❌ Supadata 回傳空逐字稿 ({video_id})")
            return None

        if isinstance(content, str):
            # text=true 模式，直接返回文字
            return content

        # 結構化模式：[{"text": "...", "offset": 0, "duration": 1500}]
        if save_to_file:
            try:
                serializable = [
                    {
                        "text": item.get("text", ""),
                        "start": item.get("offset", 0) / 1000.0,
                        "duration": item.get("duration", 0) / 1000.0,
                    }
                    for item in content
                ]
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(serializable, f, ensure_ascii=False, indent=2)
                print(f"✅ 逐字稿已緩存至: {file_path}")
            except Exception as e:
                print(f"⚠️ 緩存逐字稿失敗: {e}")

        return " ".join([item.get("text", "") for item in content])

    except Exception as e:
        print(f"❌ Supadata API 獲取逐字稿失敗 ({video_id}): {e}")
        return None

def summarize_video(video_id, video_title=""):
    print(f"🤖 正在為影片產生摘要: {video_id} - {video_title}...")
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ 未設定 GEMINI_API_KEY，跳過摘要生成。")
        return None

    transcript_text = get_transcript_text(video_id, save_to_file=True)
    if not transcript_text:
        return None

    if len(transcript_text) > 100000:
        print("⚠️ 逐字稿過長，進行截斷...")
        transcript_text = transcript_text[:100000]

    try:
        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction="You are a professional analyzer that provides ONLY the Markdown output. No conversational filler.",
        )
        response = model.generate_content(
            PROMPT_TEMPLATE.format(transcript=transcript_text),
            generation_config={"temperature": 0.7},
        )
        summary = response.text
        if summary.startswith("```markdown"):
            summary = summary.replace("```markdown", "", 1)
        if summary.startswith("```"):
            summary = summary.replace("```", "", 1)
        if summary.endswith("```"):
            summary = summary.rsplit("```", 1)[0]
        return summary.strip()
    except Exception as e:
        print(f"❌生成摘要時發生錯誤: {e}")
        return None

def save_summary(video_id, content):
    filename = f"summary_{video_id}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 摘要已儲存至: {filename}")
