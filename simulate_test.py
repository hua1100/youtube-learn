import json

STATE_FILE = "monitor_state.json"

# Target Channel: AI Engineer (k8cnVCMYmNc is the latest)
CHANNEL_URL = "https://www.youtube.com/@aiDotEngineer"

try:
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)

    if CHANNEL_URL in state:
        print(f"Before: {state[CHANNEL_URL]}")
        
        # Roll back to the previous video (or None to force re-fetch of latest)
        # Assuming we want to re-trigger the latest one 'k8cnVCMYmNc'
        # We set last_video_link to something old or None.
        # Setting to None will make it think it's INIT mode (only fetch latest 1)
        # But `monitor_task.py` logic says: if Init (no last_video_link), break after 1.
        # So setting accessing to None is perfect to re-discover the top video.
        
        state[CHANNEL_URL]['last_video_link'] = "https://old.link/dummy" 
        state[CHANNEL_URL]['last_video_title'] = "Dummy Old Video"
        
        print(f"After (Rolled Back): {state[CHANNEL_URL]}")

        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        print("✅ State rolled back. Run monitor_task.py now to test.")
    else:
        print("❌ Channel not found in state.")

except Exception as e:
    print(f"❌ Error: {e}")
