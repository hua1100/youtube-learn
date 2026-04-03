from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import json
import os
import sys
import io
import zipfile
import base64
import secrets
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

# Add 'tasks' module path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from tasks.monitor_task import check_updates, load_channels, save_channels, get_channel_id_from_url

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

# === Basic Auth Middleware ===
class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        password = os.getenv("DASHBOARD_PASSWORD")
        if not password:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth[6:]).decode("utf-8")
                provided_username, provided_password = decoded.split(":", 1)
                username = os.getenv("DASHBOARD_USERNAME", "admin")
                if (secrets.compare_digest(provided_username, username) and
                        secrets.compare_digest(provided_password, password)):
                    return await call_next(request)
            except Exception:
                pass

        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="YouTube Learn"'},
        )

# Config
DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)
VIDEOS_FILE = os.path.join(DATA_DIR, "videos.json")
SUMMARY_DIR = DATA_DIR

app.add_middleware(BasicAuthMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Level 1 Observability: Metrics Middleware ===
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

@app.get("/api/debug/auth")
def debug_auth():
    password = os.getenv("DASHBOARD_PASSWORD")
    return {"DASHBOARD_PASSWORD_set": password is not None, "value_length": len(password) if password else 0}

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
        summary_path = os.path.join(DATA_DIR, f"summary_{v['id']}.md")
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
    filename = os.path.join(DATA_DIR, f"summary_{video_id}.md")
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

class ChatRequest(BaseModel):
    video_id: str
    messages: List[dict] # [{"role": "user", "content": "..."}]

from fastapi.responses import StreamingResponse

from tasks.rag_service import chat_with_transcript_stream
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

    if not gemini_key:
        raise HTTPException(status_code=500, detail="未設定 GEMINI_API_KEY。")

    async def generate():
        try:
            transcript_text = get_transcript_text(video_id, save_to_file=True)
            if not transcript_text:
                yield "[Error: 找不到逐字稿]"
                return

            for chunk in chat_with_transcript_stream(transcript_text, messages):
                yield chunk

        except Exception as e:
            print(f"Chat Error: {e}")
            yield f"\n[Error: {str(e)}]"

    return StreamingResponse(generate(), media_type="text/event-stream")

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


@app.get("/api/channels")
def get_channels_api():
    return load_channels()

class ChannelAddRequest(BaseModel):
    url: str

@app.post("/api/channels")
def add_channel(req: ChannelAddRequest):
    url = req.url.strip().rstrip("/")
    if not url.startswith("https://www.youtube.com/"):
        raise HTTPException(status_code=400, detail="請輸入有效的 YouTube 頻道網址")
    channels = load_channels()
    if url in channels:
        raise HTTPException(status_code=409, detail="此頻道已在追蹤清單中")
    channels.append(url)
    save_channels(channels)
    return {"ok": True, "channels": channels}

@app.delete("/api/channels")
def remove_channel(req: ChannelAddRequest):
    channels = load_channels()
    url = req.url.strip().rstrip("/")
    if url not in channels:
        raise HTTPException(status_code=404, detail="找不到此頻道")
    channels.remove(url)
    save_channels(channels)
    return {"ok": True, "channels": channels}

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

@app.get("/api/export")
def export_data():
    """臨時：打包所有資料為 zip 下載"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(DATA_DIR):
            fpath = os.path.join(DATA_DIR, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, fname)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=youtube_learn_backup.zip"}
    )

@app.post("/api/reset")
def reset_system():
    """
    DANGER: Clears all data to allow full re-ingestion.
    """
    global is_update_running
    if is_update_running:
        raise HTTPException(status_code=400, detail="Cannot reset while update is running.")

    files_to_remove = [VIDEOS_FILE,
                       os.path.join(DATA_DIR, "monitor_state.json"),
                       os.path.join(DATA_DIR, "new_videos.txt")]
    for f in os.listdir(DATA_DIR):
        if f.startswith("summary_") and f.endswith(".md"):
            files_to_remove.append(os.path.join(DATA_DIR, f))

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

class StaticCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/assets/"):
            # Vite 產出的 assets 都有 content hash，可以永久快取
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif path == "/" or path.endswith(".html"):
            # HTML 不快取，確保總是拿到最新版
            response.headers["Cache-Control"] = "no-cache"
        return response

if os.path.exists(DIST_DIR):
    print(f"✅ Mounting static files from: {DIST_DIR}")
    app.add_middleware(StaticCacheMiddleware)
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
else:
    print(f"⚠️ Warning: dashboard/dist not found at: {DIST_DIR}")
    print("Run 'npm run build' in dashboard/ folder.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
