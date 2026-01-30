import sys
import os

sys.path.append(os.getcwd())

from tasks.summarizer import summarize_video

video_id = "oPBN-QIfLaY"
print(f"Summarizing {video_id}...")
try:
    summary = summarize_video(video_id, "Vibe Check: Claude Cowork Is Claude Code for the Rest of Us")
    if summary:
        print("Success!")
        print(summary[:100])
    else:
        print("Failed: No summary returned.")
except Exception as e:
    print(f"Exception: {e}")
