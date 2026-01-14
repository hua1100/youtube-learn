import json
import re
import os

OUTPUT_FILE = "new_videos.txt"
HISTORY_FILE = "videos.json"

def init_db():
    if not os.path.exists(OUTPUT_FILE):
        print("No new_videos.txt found.")
        return

    videos = []
    
    # Check existing
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                videos = json.load(f)
        except:
            pass
    
    existing_ids = {v['id'] for v in videos}

    with open(OUTPUT_FILE, 'r') as f:
        for line in f:
            # Line format: [Timestamp] New Video: Title - Link
            # Example: [2026-01-13 23:26:18] New Video: "Pain is the new moat" - https://www.youtube.com/shorts/K4rMYsAsSEI
            # Needs robust regex
            match = re.search(r'New Video: (.+) - (https?://.+)', line)
            if match:
                title = match.group(1).strip()
                link = match.group(2).strip()
                
                # Extract ID
                vid_id = None
                if 'youtube.com/watch?v=' in link:
                    vid_id = link.split('v=')[1].split('&')[0]
                elif 'youtu.be/' in link:
                    vid_id = link.split('youtu.be/')[1].split('?')[0]
                elif 'youtube.com/shorts/' in link:
                    vid_id = link.split('shorts/')[1].split('?')[0]
                
                if vid_id and vid_id not in existing_ids:
                    videos.append({
                        'id': vid_id,
                        'title': title,
                        'link': link,
                        'published': "" # Unknown from txt
                    })
                    print(f"Added: {title}")
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    print(f"Database initialized with {len(videos)} videos.")

if __name__ == "__main__":
    init_db()
