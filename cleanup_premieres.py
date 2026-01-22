import json
import os

VIDEOS_FILE = "videos.json"
STATE_FILE = "monitor_state.json"

IDS_TO_REMOVE = ["5YBjll9XJlw"]

def clean_videos():
    if not os.path.exists(VIDEOS_FILE):
        print("videos.json not found.")
        return

    with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    initial_count = len(videos)
    # Filter out the specific IDs
    videos = [v for v in videos if v['id'] not in IDS_TO_REMOVE]
    final_count = len(videos)

    if initial_count != final_count:
        with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        print(f"✅ Removed {initial_count - final_count} videos from {VIDEOS_FILE}")
    else:
        print(f"⚠️ No matching videos found in {VIDEOS_FILE}")

def clean_state():
    if not os.path.exists(STATE_FILE):
        print("monitor_state.json not found.")
        return

    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)

    modified = False
    for channel, data in state.items():
        last_link = data.get('last_video_link')
        if not last_link:
            continue
        
        # Check if the last seen video is one of the ones we are removing
        for vid_id in IDS_TO_REMOVE:
            if vid_id in last_link:
                print(f"🔄 Resetting state for channel {channel} (was {vid_id})")
                data['last_video_link'] = None
                data['last_video_title'] = None
                data['last_checked'] = None # Force re-check
                modified = True
                break
    
    if modified:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        print(f"✅ Updated {STATE_FILE} to forget removed videos.")
    else:
        print(f"ℹ️ No state reset needed (removed videos were not satisfied as latest state).")

if __name__ == "__main__":
    clean_videos()
    clean_state()
