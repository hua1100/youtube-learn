import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from tasks.monitor_task import get_latest_video, get_channel_id_from_url

url = "https://www.youtube.com/@Google/videos"
channel_id = get_channel_id_from_url(url)
print(f"Channel ID: {channel_id}")

if channel_id:
    video = get_latest_video(channel_id)
    print(f"Latest Non-Short Video found: {video}")
