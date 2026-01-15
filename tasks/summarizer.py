import os
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
 <highlight> 以"## 精煉亮點"為標題，用一句深刻且有啟發性的話總結整個訪談的核心價值。請根據影片的具體內容，提煉出最獨特、最具洞察力的一個觀點，避免使用套路化的句式，直接切入核心思想。 </highlight> 
請確保你的分析全面、準確，並且以流暢的中文表達。你的摘要應該能夠幫助讀者快速理解訪談的核心內容，而一句話的亮點總結應該能夠激發讀者的思考。輸出時請直接使用Markdown格式，不要包含任何XML標籤。

影片逐字稿如下：
{transcript}
"""

def get_transcript_text(video_id):
    try:
        # 使用新版 API (v1.2.3+ or similar variant)
        # 根據 debug，它是 class 且有 fetch 方法
        yt_api = YouTubeTranscriptApi()
        transcript_obj = yt_api.fetch(video_id, languages=['zh-TW', 'zh', 'en'])
        
        # 轉換為純文字
        if transcript_obj:
            # 根據報錯 'FetchedTranscriptSnippet object is not subscriptable'
            # 這代表回傳的是物件列表，要用 .text 屬性存取
            full_text = " ".join([snippet.text for snippet in transcript_obj])
            return full_text
        return None
    except Exception as e:
        print(f"❌ 無法獲取逐字稿 ({video_id}): {e}")
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

    transcript_text = get_transcript_text(video_id)
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
        return summary
    except Exception as e:
        print(f"❌生成摘要時發生錯誤: {e}")
        return None

def save_summary(video_id, content):
    filename = f"summary_{video_id}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 摘要已儲存至: {filename}")
