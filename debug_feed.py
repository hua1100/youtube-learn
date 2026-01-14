import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from tasks.monitor_task import get_new_videos, get_channel_id_from_url

url = "https://www.youtube.com/@Google/videos"
channel_id = get_channel_id_from_url(url)
print(f"Channel ID: {channel_id}")

if channel_id:
    # Init mode (no last_link), returns list with latest video
    videos = get_new_videos(channel_id)
    print(f"Found {len(videos)} new videos:")
    for v in videos:
        print(v)
