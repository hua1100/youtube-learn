import os
import json
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

PROMPT_TEMPLATE = """
你是一個專業的影片內容分析助手。你的任務是分析youtube影片，並提供中文摘要。請仔細閱讀以下文字稿，然後按照指示完成任務：
請按照以下步驟進行分析：
1. 仔細觀看影片，確保你理解了訪談的整體內容和主題。
2. 識別並提取影片中的所有問題。將這些問題列出來，並根據內容進行分類整理。
3. 根據問題和回答，提供一個有條理、邏輯清晰的中文摘要。這個摘要應該涵蓋訪談的主要觀點和討論的關鍵話題。
4. 用一句話總結整個影片的亮點。這句話應該精煉、有洞察力，並能給人啟發。
請將你的分析輸出為Markdown格式，不要使用XML標籤，按照以下結構和範例：
 <summary> 以"## 內容摘要"為標題，提供全面而深入的摘要，包含背景、核心觀點、具體案例和解決方案 </summary> <example> 這是一期關於AI應用開發的深度訪談，嘉賓Pete Kumman（YC合夥人、Optimizely創始人）批評了當前AI產品開發的問題。他指出許多AI應用（如Gmail的AI寫郵件功能）雖然底層模型強大，但用戶體驗糟糕，原因是開發者仍在用傳統軟件開發思維來構建AI功能。 Pete認為問題的核心在於：開發者將系統提示詞（system prompt）當作代碼一樣隱藏起來，導致AI輸出千篇一律、不符合個人風格。他提出了"AI馬車"概念，類比早期汽車設計只是在馬車上裝引擎，沒有發揮新技術的真正潛力。 解決方案是讓用戶能夠查看和編輯系統提示詞，將AI從"一刀切"的工具變成可個人化定制的助手。Pete演示了如何通過自定義系統提示詞讓AI以個人化的語調寫郵件，以及構建智能郵件處理代理來自動化重複性工作。 他強調未來的AI應用應該專注於提供強大的工具集，讓AI代理能夠跨平台執行任務，真正實現工作自動化，而不是僅僅停留在聊天機器人層面。 </example> <questions> 以"## 主要問題"為標題，用數字列表格式列出訪談中的關鍵問題，應該涵蓋不同層面和角度 </questions> <example> 1. 為什麼Gmail等智能應用的AI功能體驗糟糕？ 2. 聰明的Google工程師為什麼會開發出用戶不喜歡的功能？ 3. 什麼是"AI馬車"概念？ 4. 如何解決AI輸出不符合個人風格的問題？ 5. 普通用戶是否能夠編寫系統提示詞？ 6. 為什麼編程AI工具（如Cursor）比其他AI應用更成功？ 7. 開發者應該專注於構建什麼樣的AI工具？ 8. 創業者如何重新思考AI原生產品的設計？ </example> 
<organized_content> 以"## 有條理的內容整理"為標題，用粗體子標題分類整理內容，每個分類下用項目符號詳細說明 </organized_content> <example> 問題診斷
* 體驗割裂：AI編程工具（Cursor、Windsurf）讓人感覺超能力，而其他AI應用卻增加工作負擔
* Gmail案例分析：AI寫郵件功能產生的郵件既不像用戶風格，寫提示詞的時間也不比直接寫郵件省時
* 根本原因：開發者用傳統軟件開發思維構建AI功能，將系統提示詞當作代碼隱藏起來
核心概念
* AI馬車現象：就像早期汽車只是在馬車上裝引擎，當前AI應用只是在舊軟件上嵌入AI，沒有發揮真正潛力
* 系統提示詞的重要性：決定AI行為和輸出風格的關鍵，但被開發者隱藏，導致千篇一律的輸出
* 一刀切vs個人化：傳統軟件必須服務所有用戶，但AI可以為每個用戶定制
解決方案
* 開放系統提示詞：讓用戶能查看和編輯，實現個人化定制
* 漸進式學習：AI通過歷史數據和用戶反饋自動優化系統提示詞
* 工具生態系統：為AI代理提供豐富的工具集，實現跨平台自動化 </example>
 <highlight> 以"## 精煉亮點"為標題，用一句具體的「行動指引」來總結。想像你是讀者的導師，看完影片後，你會建議他立刻去做什麼改變？請用「動詞」開頭，具體描述該採取的行動或該改變的認知。 </highlight> 
請確保你的分析全面、準確，並且以流暢的中文表達。你的摘要應該能夠幫助讀者快速理解訪談的核心內容，而一句話的亮點總結應該能夠激發讀者的思考。輸出時請直接使用Markdown格式，不要包含任何XML標籤。

影片逐字稿如下：
{transcript}
"""


def get_transcript_text(video_id, save_to_file=False):
    """
    獲取逐字稿文字。
    :param video_id: YouTube Video ID
    :param save_to_file: 是否儲存為 JSON 檔案 (transcripts/{video_id}.json)
    :return: 逐字稿純文字 string or None
    """
    # 1. Check if local file exists
    transcript_dir = os.path.join(os.path.dirname(__file__), "..", "transcripts")
    os.makedirs(transcript_dir, exist_ok=True)
    file_path = os.path.join(transcript_dir, f"{video_id}.json")

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 兼容舊格式或直接儲存 plain text 的情況 (雖然後面我們打算存 list struct)
                # 這裡簡單起見，我們如果存的是 raw list of dicts from youtube_transcript_api
                if isinstance(data, list):
                    return " ".join([item.get('text', '') for item in data])
                elif isinstance(data, dict) and 'text' in data:
                    return data['text']
        except Exception as e:
            print(f"⚠️ 讀取本地逐字稿失敗 ({video_id}): {e}")

    try:
        # 使用新版 API (v1.2.3+ or similar variant)
        # 根據 debug，它是 class 且有 fetch 方法
        yt_api = YouTubeTranscriptApi()
        transcript_obj = yt_api.fetch(video_id, languages=['zh-TW', 'zh', 'en'])
        
        # transcript_obj is a list of dicts: [{'text': '...', 'start': 0.0, 'duration': 1.0}, ...]
        if transcript_obj:
            # Save to file if requested
            if save_to_file:
                try:
                    # Save the raw structured data for future potential use (timestamps etc)
                    # Convert to list if it isn't already (fetch usually returns a list-like object)
                    # Depending on library version, it might be a specific object type, but usually valid list of dicts.
                    # We will serialise it.
                    serializable = []
                    for item in transcript_obj:
                        serializable.append({
                            'text': item.text if hasattr(item, 'text') else item.get('text'),
                            'start': item.start if hasattr(item, 'start') else item.get('start'),
                            'duration': item.duration if hasattr(item, 'duration') else item.get('duration')
                        })
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(serializable, f, ensure_ascii=False, indent=2)
                        print(f"✅ 逐字稿已緩存至: {file_path}")
                except Exception as e:
                    print(f"⚠️ 緩存逐字稿失敗: {e}")

            # Return text
            full_text = " ".join([snippet.text for snippet in transcript_obj])
            return full_text
        return None
    except Exception as e:
        print(f"❌ 傳統 API 獲取逐字稿失敗 ({video_id}): {e}")
        print("🔄 嘗試使用 yt-dlp 備援機制...")
        
        try:
            import yt_dlp
            
            url = f"https://www.youtube.com/watch?v={video_id}"
            ydl_opts = {
                'skip_download': True,
                'writeautomaticsub': True,
                'writesubtitles': True,
                'subtitleslangs': ['zh-TW', 'zh', 'en'],
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Check for subtitles or automatic captions
                subtitles = info.get('subtitles', {}) or info.get('automatic_captions', {})
                
                # Prioritize Traditional Chinese -> Chinese -> English
                lang_priority = ['zh-TW', 'zh-Hant', 'zh', 'zh-Hans', 'en']
                selected_lang = None
                
                for lang in lang_priority:
                     if lang in subtitles:
                         selected_lang = lang
                         break
                
                if not selected_lang and subtitles:
                    selected_lang = list(subtitles.keys())[0]
                    
                if selected_lang:
                    print(f"✅ 找到字幕語言: {selected_lang}")
                    
                    # Use yt-dlp to download subtitles to a temporary file
                    # We need to re-configure ydl for downloading specific sub
                    try:
                        temp_filename = f"temp_sub_{video_id}"
                        ydl_opts_download = {
                            'skip_download': True,
                            'writesubtitles': True,
                            'writeautomaticsub': True,
                            'subtitleslangs': [selected_lang],
                            'outtmpl': temp_filename,
                            'quiet': True,
                            'no_warnings': True,
                            'extractor_args': {'youtube': {'player_client': ['android']}},
                        }
                        
                        with yt_dlp.YoutubeDL(ydl_opts_download) as ydl_down:
                            ydl_down.download([url])
                        
                        # Find the downloaded file
                        # yt-dlp appends language code: temp_sub_{video_id}.zh-Hant.vtt
                        expected_file = f"{temp_filename}.{selected_lang}.vtt"
                        
                        if not os.path.exists(expected_file):
                             # Try guessing other extensions or lang codes if exact match fails
                             for f in os.listdir('.'):
                                 if f.startswith(temp_filename) and f.endswith('.vtt'):
                                     expected_file = f
                                     break
                        
                        if os.path.exists(expected_file):
                            with open(expected_file, 'r', encoding='utf-8') as f:
                                raw_content = f.read()
                            
                            # Clean up
                            os.remove(expected_file)
                            
                            # VTT Parsing
                            lines = raw_content.splitlines()
                            text_lines = []
                            for line in lines:
                                if '-->' in line or line.strip() == 'WEBVTT' or not line.strip():
                                    continue
                                text_lines.append(line.strip())
                            
                            # Remove duplicates/headers if any
                            # Filter out style tags or similar if needed, but basic buffer is fine
                            unique_lines = []
                            last = ""
                            for line in text_lines:
                                if line != last:
                                    unique_lines.append(line)
                                    last = line
                                    
                            return " ".join(unique_lines)
                        else:
                             print(f"❌ 無法找到下載的字幕檔案: {expected_file}")

                    except Exception as dl_err:
                        print(f"❌ yt-dlp 下載流程失敗: {dl_err}")
                
        except Exception as yt_e:
            print(f"❌ yt-dlp 備援失敗: {yt_e}")
            return None

def summarize_video(video_id, video_title=""):
    print(f"🤖 正在為影片產生摘要: {video_id} - {video_title}...")
    
    # Check for API Key
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    
    if not api_key or not base_url:
        print("⚠️ 未設定 LLM_API_KEY 或 LLM_BASE_URL，跳過摘要生成。")
        return None

    transcript_text = get_transcript_text(video_id, save_to_file=True)
    if not transcript_text:
        return None
    
    # Truncate if too long (simple check, assume reasonable context window for local LLM)
    if len(transcript_text) > 100000:
        print("⚠️ 逐字稿過長，進行截斷...")
        transcript_text = transcript_text[:100000]

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": PROMPT_TEMPLATE.format(transcript=transcript_text)}
            ],
            temperature=0.7
        )
        
        summary = response.choices[0].message.content
        
        # Clean up markdown fences if present
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
