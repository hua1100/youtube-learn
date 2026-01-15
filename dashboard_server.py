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
if os.path.exists("dashboard/dist"):
    app.mount("/", StaticFiles(directory="dashboard/dist", html=True), name="static")
else:
    print("⚠️ Warning: dashboard/dist not found. Run 'npm run build' in dashboard/ folder.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
