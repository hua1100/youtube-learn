import os
import json
import time
import logging
from dotenv import load_dotenv
from google import genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Env
load_dotenv()
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

RAG_MAP_FILE = "rag_map.json"

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
            myfile = _client.files.get(name=file_name)
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

    myfile = _client.files.upload(
        file=upload_path,
        config={"mime_type": mime_type, "display_name": f"transcript_{video_id}"},
    )

    # Wait for processing
    while myfile.state.name == "PROCESSING":
        time.sleep(1)
        myfile = _client.files.get(name=myfile.name)

    if myfile.state.name != "ACTIVE":
        raise Exception(f"File upload failed with state: {myfile.state.name}")

    logger.info(f"Upload complete: {myfile.name}")

    rag_map[video_id] = myfile.name
    save_rag_map(rag_map)

    return myfile

def is_file_indexed(video_id):
    rag_map = load_rag_map()
    return video_id in rag_map

def chat_with_store_stream(file_obj_or_name, messages, model_name="gemini-1.5-flash"):
    """
    Streams chat response using Gemini Long Context (passing file directly).
    """
    if isinstance(file_obj_or_name, str):
        file_obj = _client.files.get(name=file_obj_or_name)
    else:
        file_obj = file_obj_or_name

    last_user_message = messages[-1]['content']
    logger.info(f"Querying Gemini (Long Context) with file {file_obj.name}...")

    system_instruction = """You are a professional research assistant analyzing a video transcript.

    Rules:
    1. Answer the user's question based on the provided video transcript.
    2. If the answer is not explicitly stated, try to infer it from the context. If you still can't find it, state that it's not in the transcript.
    3. Output in Traditional Chinese (繁體中文/台灣用語) naturally.
    4. Provide comprehensive and helpful answers.
    """

    response = _client.models.generate_content_stream(
        model=model_name,
        contents=[last_user_message, file_obj],
        config={"system_instruction": system_instruction},
    )

    for chunk in response:
        if chunk.text:
            yield chunk.text
