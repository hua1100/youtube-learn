import os
import json
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

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
    Returns the file object (or name).
    """
    rag_map = load_rag_map()
    
    # 1. Check existing file
    if video_id in rag_map:
        file_name = rag_map[video_id] # This is the "files/..." resource name
        logger.info(f"Checking existing file for {video_id}: {file_name}")
        try:
            # Check if file exists and is active
            myfile = genai.get_file(file_name)
            if myfile.state.name == "ACTIVE":
                return myfile
            else:
                logger.info(f"File {file_name} is in state {myfile.state.name}, recreating.")
        except Exception as e:
            logger.warning(f"File {file_name} not found remotely (expired?), recreating. Error: {e}")
    
    # 2. Upload new file
    logger.info(f"Uploading new file for video {video_id}...")
    
    # Ensure path
    if not os.path.isabs(transcript_path):
        transcript_path = os.path.abspath(transcript_path)

    # Convert JSON to Text to match Gemini Long Context requirements (text/plain preference)
    # and to reduce token usage/noise from JSON syntax.
    txt_path = transcript_path.replace(".json", ".txt")
    
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Format: [00:00.000] Text content...
        text_content = ""
        # Handle different transcript formats (list of dicts typically)
        if isinstance(data, list):
            for item in data:
                start = item.get('start', 0)
                text = item.get('text', '')
                # Simple formatting
                text_content += f"[{start}] {text}\n"
        else:
            # Fallback if it's not a list (maybe already text or other format?)
            text_content = str(data)
            
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)
            
        upload_path = txt_path
        mime_type = "text/plain"
        
    except Exception as e:
        logger.warning(f"Failed to convert JSON to TXT: {e}. Falling back to original file.")
        upload_path = transcript_path
        mime_type = "application/json"

    # Upload with specific MIME type
    myfile = genai.upload_file(upload_path, mime_type=mime_type, display_name=f"transcript_{video_id}")
    
    # Wait for processing
    while myfile.state.name == "PROCESSING":
        time.sleep(1)
        myfile = genai.get_file(myfile.name)

    if myfile.state.name != "ACTIVE":
        raise Exception(f"File upload failed with state: {myfile.state.name}")
        
    logger.info(f"Upload complete: {myfile.name}")
    
    # Save mapping (store the resource name 'files/...')
    rag_map[video_id] = myfile.name
    save_rag_map(rag_map)
    
    return myfile

def chat_with_store_stream(file_obj_or_name, messages, model_name="gemini-2.0-flash"):
    """
    Streams chat response using Gemini Long Context (passing file directly).
    """
    # If we got a string (name) from somewhere else, fetch the object
    if isinstance(file_obj_or_name, str):
        file_obj = genai.get_file(file_obj_or_name)
    else:
        file_obj = file_obj_or_name

    # Extract prompt
    last_user_message = messages[-1]['content']
    
    logger.info(f"Querying Gemini (Long Context) with file {file_obj.name}...")

def is_file_indexed(video_id):
    """
    Checks if we have a valid active file for this video.
    """
    rag_map = load_rag_map()
    if video_id in rag_map:
        # We assume if it's in the map, it's likely fine. 
        # For strictness we could checking state, but that adds latency.
        # Let's trust the map for the UI hint, get_or_create will handle the real check.
        return True
    return False

def chat_with_store_stream(file_obj_or_name, messages, model_name="gemini-2.0-flash"):
    """
    Streams chat response using Gemini Long Context (passing file directly).
    """
    # If we got a string (name) from somewhere else, fetch the object
    if isinstance(file_obj_or_name, str):
        file_obj = genai.get_file(file_obj_or_name)
    else:
        file_obj = file_obj_or_name

    # Extract prompt
    last_user_message = messages[-1]['content']
    
    logger.info(f"Querying Gemini (Long Context) with file {file_obj.name}...")

    # System instruction for language consistency and behavior
    # Refined to allow context interpretation while maintaining accuracy
    system_instruction = """You are a professional research assistant analyzing a video transcript.
    
    Rules:
    1. Answer the user's question based on the provided video transcript.
    2. If the answer is not explicitly stated, try to infer it from the context. If you still can't find it, state that it's not in the transcript.
    3. Output in Traditional Chinese (繁體中文/台灣用語) naturally.
    4. Provide comprehensive and helpful answers.
    """
    model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
    
    # Context Stuffing: [Prompt, File]
    # We can also construct a ChatSession if we want history, 
    # but for now, [Prompt, File] is robust for Q&A.
    
    response = model.generate_content(
        [last_user_message, file_obj],
        stream=True
    )
    
    for chunk in response:
        if chunk.text:
            yield chunk.text
