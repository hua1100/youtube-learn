import os
import json
import time
import logging
from dotenv import load_dotenv
from tasks.gemini_client import get_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Env
load_dotenv()

RAG_MAP_FILE = "/app/data/rag_map.json"

def load_rag_map():
    if os.path.exists(RAG_MAP_FILE):
        try:
            with open(RAG_MAP_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_rag_map(data):
    with open(RAG_MAP_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_or_create_store(video_id, transcript_path):
    """
    Ensures the transcript is uploaded to Gemini Files API.
    Returns the file object.
    """
    rag_map = load_rag_map()

    # 1. Check existing file
    if video_id in rag_map:
        file_name = rag_map[video_id]
        logger.info(f"Checking existing file for {video_id}: {file_name}")
        try:
            myfile = get_client().files.get(name=file_name)
            if myfile.state.name == "ACTIVE":
                return myfile
            else:
                logger.info(f"File {file_name} is in state {myfile.state.name}, recreating.")
        except Exception as e:
            logger.warning(f"File {file_name} not found remotely (expired?), recreating. Error: {e}")

    # 2. Upload new file
    logger.info(f"Uploading new file for video {video_id}...")

    if not os.path.isabs(transcript_path):
        transcript_path = os.path.abspath(transcript_path)

    txt_path = transcript_path.replace(".json", ".txt")

    try:
        if not os.path.exists(txt_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            text_content = ""
            if isinstance(data, list):
                for item in data:
                    start = item.get('start', 0)
                    text = item.get('text', '')
                    text_content += f"[{start}] {text}\n"
            else:
                text_content = str(data)

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text_content)

        upload_path = txt_path
        mime_type = "text/plain"

    except Exception as e:
        logger.warning(f"Failed to convert JSON to TXT: {e}. Falling back to original file.")
        upload_path = transcript_path
        mime_type = "application/json"

    myfile = get_client().files.upload(
        file=upload_path,
        config={"mime_type": mime_type, "display_name": f"transcript_{video_id}"},
    )

    # Wait for processing
    while myfile.state.name == "PROCESSING":
        time.sleep(1)
        myfile = get_client().files.get(name=myfile.name)

    if myfile.state.name != "ACTIVE":
        raise Exception(f"File upload failed with state: {myfile.state.name}")

    logger.info(f"Upload complete: {myfile.name}")

    rag_map[video_id] = myfile.name
    save_rag_map(rag_map)

    return myfile

def chat_with_transcript_stream(transcript_text: str, messages: list, model_name: str = "gemini-2.5-flash"):
    """
    直接把逐字稿文字塞進 prompt 進行對話，不需要 Files API。
    Gemini 2.5-flash 有 1M token context，足以容納完整逐字稿。
    """
    last_user_message = messages[-1]['content']

    prompt = f"""你是一位專業的影片逐字稿分析助手。

規則：
1. 根據下方提供的逐字稿內容回答問題。
2. 若答案未明確提及，嘗試從上下文推斷；若真的找不到，明確說明。
3. 用繁體中文（台灣用語）回答。
4. 提供詳盡且有幫助的回答。

===逐字稿內容===
{transcript_text}
================

使用者問題：{last_user_message}"""

    response = get_client().models.generate_content_stream(
        model=model_name,
        contents=prompt,
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text
