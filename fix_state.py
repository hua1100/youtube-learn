import json

STATE_FILE = "monitor_state.json"

try:
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # Update YCombinator
    state["https://www.youtube.com/@ycombinator"] = {
        "channel_id": "UCcefcZRL2oaA_uBNeo5UOWg",
        # Clear others to force refresh
        "last_video_link": None, 
        "last_video_title": None,
        "last_checked": None
    }

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    print("✅ Fixed monitor_state.json")

except Exception as e:
    print(f"❌ Error: {e}")
