from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os
import sys
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

# Add 'tasks' module path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from tasks.monitor_task import check_updates

# Initialize Scheduler
scheduler = BackgroundScheduler()

# Global state for update status (Must be defined before lifespan uses run_update_wrapper)
is_update_running = False
last_update_result = None

def run_update_wrapper():
    global is_update_running, last_update_result
    is_update_running = True
    try:
        count = check_updates()
        last_update_result = {"count": count, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        print(f"Update failed: {e}")
    finally:
        is_update_running = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start scheduler
    print("⏰ Starting Scheduler...")
    # Schedule check_updates every 1 hour (3600 seconds)
    # Using run_update_wrapper to ensure state consistency
    scheduler.add_job(run_update_wrapper, 'interval', hours=4, id='check_updates_job')
    scheduler.start()
    yield
    # Shutdown: Stop scheduler
    print("⏰ Stopping Scheduler...")
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Config
VIDEOS_FILE = "videos.json"
SUMMARY_DIR = "."

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Level 1 Observability: Metrics Middleware ===
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

# Metrics Storage (In-Memory)
metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "last_request_time": None,
    "avg_latency_ms": 0.0,
    "uptime_start": datetime.now().isoformat()
}

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Track Request
        metrics["total_requests"] += 1
        metrics["last_request_time"] = datetime.now().isoformat()
        
        try:
            response = await call_next(request)
            
            # Track Error (HTTP 500+)
            if response.status_code >= 500:
                metrics["total_errors"] += 1
                
            return response
        except Exception as e:
            # Track Unhandled Exception
            metrics["total_errors"] += 1
            raise e
        finally:
            # Calculate Latency
            process_time = (time.time() - start_time) * 1000 # ms
            
            # Simple moving average for latency (to keep it stable but responsive)
            # New Avg = 0.9 * Old + 0.1 * New
            if metrics["avg_latency_ms"] == 0:
                 metrics["avg_latency_ms"] = process_time
            else:
                 metrics["avg_latency_ms"] = (metrics["avg_latency_ms"] * 0.9) + (process_time * 0.1)

app.add_middleware(MetricsMiddleware)

@app.get("/api/health_stats")
def get_health_stats():
    """
    Expose monitoring metrics for the dashboard.
    """
    return {
        "status": "healthy",
        "metrics": metrics,
        "scheduler_running": scheduler.running
    }
# ===============================================

class Video(BaseModel):
    id: str
    title: str
    link: str
    published: Optional[str] = None
    channel_title: Optional[str] = None
    has_summary: bool = False
    is_read: bool = False

@app.get("/api/videos", response_model=List[dict])
def get_videos():
    videos = []
    if os.path.exists(VIDEOS_FILE):
        try:
            with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
                videos = json.load(f)
        except Exception as e:
            print(f"Error loading videos: {e}")
    
    # Enrich with summary data
    results = []
    for v in videos:
        summary_path = f"summary_{v['id']}.md"
        v['has_summary'] = os.path.exists(summary_path)
        v['preview'] = ""
        v['highlight'] = ""
        v['tags'] = []
        
        if v['has_summary']:
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract Preview (approximate: text after '## 內容摘要')
                    if "## 內容摘要" in content:
                        part = content.split("## 內容摘要")[1].split("## ")[0]
                        # Remove markdown bold/italic/links for clean text
                        clean_text = part.replace('*', '').replace('#', '').strip()
                        v['preview'] = clean_text[:200] + "..." if len(clean_text) > 200 else clean_text
                    
                    # Extract Highlight (approximate: text after '## 精煉亮點')
                    if "## 精煉亮點" in content:
                         highlight_part = content.split("## 精煉亮點")[1].strip()
                         v['highlight'] = highlight_part.split('\n')[0].replace('*', '').strip()
                    # Extract Tags (approximate: text after '## 標籤' or 'Tags')
                    if "## 標籤" in content:
                        tags_part = content.split("## 標籤")[1].split("##")[0]
                        v['tags'] = [t.strip().replace('#', '') for t in tags_part.split() if t.strip()]
                    elif "## Tags" in content: 
                         tags_part = content.split("## Tags")[1].split("##")[0]
                         v['tags'] = [t.strip().replace('#', '') for t in tags_part.split() if t.strip()]
                    
                    # If extraction failed, add mock tags based on title/channel
                    if not v['tags']:
                         if "AI" in v['title'] or "Intelligence" in v['title']:
                             v['tags'].append("Artificial Intelligence")
                         if "Python" in v['title']:
                             v['tags'].append("Python")
                         if not v['tags']:
                             v['tags'] = ["Tech", "Software"]

            except:
                pass
                
        results.append(v)
    
    return results

@app.get("/api/summary/{video_id}")
def get_summary(video_id: str):
    filename = f"summary_{video_id}.md"
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Summary not found")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/videos/{video_id}/toggle_read")
def toggle_read(video_id: str):
    if not os.path.exists(VIDEOS_FILE):
        raise HTTPException(status_code=404, detail="No videos database found")
    
    try:
        updated_video = None
        with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        
        for v in videos:
            if v['id'] == video_id:
                # Toggle current state, default to False if missing
                current_state = v.get('is_read', False)
                v['is_read'] = not current_state
                updated_video = v
                break
        
        if updated_video:
            with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
            return updated_video
        else:
            raise HTTPException(status_code=404, detail="Video not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Chat API ===
from tasks.summarizer import get_transcript_text
from openai import OpenAI

# Reuse env vars for Chat
CHAT_API_KEY = os.getenv("LLM_API_KEY")
CHAT_BASE_URL = os.getenv("LLM_BASE_URL")
CHAT_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

class ChatRequest(BaseModel):
    video_id: str
    messages: List[dict] # [{"role": "user", "content": "..."}]

from fastapi.responses import StreamingResponse

from tasks.rag_service import get_or_create_store, chat_with_store_stream, is_file_indexed
from tasks.mindmap_generator import generate_mindmap, mindmap_exists as check_mindmap_exists
import os

@app.post("/api/chat")
async def chat_with_video(request: ChatRequest):
    # Determine which mode to use based on env vars
    # If GEMINI_API_KEY is present, we use RAG (File Search)
    # Otherwise, we fallback to the original context stuffing (OpenAI/Other)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    video_id = request.video_id
    messages = request.messages

    # >>> Strategy 1: Gemini RAG (Preferred if key exists) <<<
    if gemini_key:
        print(f"Using Gemini RAG for video {video_id}")
        
        # Generator for streaming RAG response
        async def rag_generate():
            try:
                # 1. Check/Prepare Knowledge Base
                # Only show status if we actually need to index
                if not is_file_indexed(video_id):
                     yield "🔄 [System] Initializing knowledge base for this video... (This happens only once)\n\n"
                     yield "---\n"
                
                # This might take a few seconds if not indexed
                transcript_path = os.path.abspath(f"transcripts/{video_id}.json")
                if not os.path.exists(transcript_path):
                     # Ensure we have the transcript first
                     get_transcript_text(video_id, save_to_file=True)
                
                # 2. Get Store (Lazy Loading) - In this mode, 'store_name' is actually a File Object or Name
                file_obj = get_or_create_store(video_id, transcript_path)
                
                # 3. Chat
                
                # Pass file_obj.name or file_obj depending on what chat_with_store_stream expects
                # Updated rag_service handles both.
                rag_stream = chat_with_store_stream(file_obj, messages)
                for chunk in rag_stream:
                    yield chunk
                    
            except Exception as e:
                print(f"RAG Error: {e}")
                yield f"\n[Error: {str(e)}]"

        return StreamingResponse(rag_generate(), media_type="text/event-stream")

    # >>> Strategy 2: Original Context Stuffing (Fallback) <<<
    if not CHAT_API_KEY or not CHAT_BASE_URL:
         raise HTTPException(status_code=500, detail="No LLM configuration found (GEMINI_API_KEY or LLM_API_KEY).")

    # ... (Keep existing Logic for OpenAI/Local LLM) ...
    transcript_text = get_transcript_text(video_id, save_to_file=True)
    if not transcript_text:
         raise HTTPException(status_code=404, detail="Transcript not available.")
         
    system_prompt = f"""
    You are an AI assistant helping a user understand a YouTube video.
    Below is the transcript.
    
    Transcript:
    {transcript_text[:200000]} 
    (Truncated if too long)
    """
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        client = OpenAI(api_key=CHAT_API_KEY, base_url=CHAT_BASE_URL)
        def generate():
            stream = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=full_messages,
                temperature=0.7,
                stream=True 
            )
            for chunk in stream:
                 if chunk.choices[0].delta.content:
                     yield chunk.choices[0].delta.content

        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

# === Mindmap API ===
@app.get("/api/mindmap/{video_id}/exists")
def get_mindmap_exists(video_id: str):
    """檢查心智圖是否已生成"""
    return {"exists": check_mindmap_exists(video_id)}

@app.get("/api/mindmap/{video_id}")
async def get_mindmap(video_id: str):
    """生成或返回快取的心智圖 Mermaid 語法"""
    try:
        mermaid_code = generate_mindmap(video_id)
        if mermaid_code:
            return {"mermaid": mermaid_code}
        else:
            raise HTTPException(status_code=404, detail="無法生成心智圖，請確認逐字稿存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成心智圖時發生錯誤: {str(e)}")


@app.get("/api/status")
def get_status():
    return {
        "is_updating": is_update_running,
        "last_update_result": last_update_result
    }

@app.post("/api/refresh")
def refresh_data(background_tasks: BackgroundTasks):
    """
    Manually trigger the update process in the background.
    """
    global is_update_running
    if is_update_running:
         return {"status": "Busy", "message": "Update already in progress."}
         
    background_tasks.add_task(run_update_wrapper)
    return {"status": "Update started", "message": "The system is checking for updates in the background."}

@app.post("/api/reset")
def reset_system():
    """
    DANGER: Clears all data to allow full re-ingestion.
    """
    global is_update_running
    if is_update_running:
        raise HTTPException(status_code=400, detail="Cannot reset while update is running.")

    # Files to remove
    files_to_remove = [VIDEOS_FILE, "monitor_state.json", "new_videos.txt"]
    
    # Remove summary files
    for f in os.listdir("."):
        if f.startswith("summary_") and f.endswith(".md"):
            files_to_remove.append(f)

    deleted = []
    for f in files_to_remove:
        if os.path.exists(f):
            try:
                os.remove(f)
                deleted.append(f)
            except Exception as e:
                print(f"Error removing {f}: {e}")
                
    return {"status": "System Reset", "deleted_files": deleted}

# Mount Frontend Static Files
# Ensure this is after API routes so they are processed first
# Mount Frontend Static Files using Absolute Path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dashboard", "dist")

if os.path.exists(DIST_DIR):
    print(f"✅ Mounting static files from: {DIST_DIR}")
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
else:
    print(f"⚠️ Warning: dashboard/dist not found at: {DIST_DIR}")
    print("Run 'npm run build' in dashboard/ folder.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
