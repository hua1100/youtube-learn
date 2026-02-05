from tasks.summarizer import summarize_video, save_summary
import os
from dotenv import load_dotenv

load_dotenv()

videos = [
    {"id": "7hnvRBjuCW8", "title": "Farming for the future | Where the Internet Lives"},
    {"id": "70ec37XHGIg", "title": "Ozempic Won't Solve America's Obesity Problem"}
]

for video in videos:
    print(f"\n--- Processing {video['id']}: {video['title']} ---")
    content = summarize_video(video['id'], video['title'])
    
    if content:
        save_summary(video['id'], content)
        print(f"✅ Success for {video['id']}")
    else:
        print(f"❌ Failed for {video['id']}")
