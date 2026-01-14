from youtube_transcript_api import YouTubeTranscriptApi, VideoUnavailable

def is_premiere(video_id):
    print(f"Checking {video_id}...", end=" ")
    try:
        # Based on previous debugging, this version uses instantiation + fetch
        # And 'fetch' is what threw the 'Premieres in' error in our logs earlier.
        yt_api = YouTubeTranscriptApi()
        yt_api.fetch(video_id)
        
        print("Not Premiere (Transcripts found)")
        return False
    except VideoUnavailable as e:
        # The library might raise VideoUnavailable OR TranscriptsDisabled OR just a general Exception with the message
        # Let's check the string representation of ANY error to be safe, but mostly VideoUnavailable
        if "Premieres in" in str(e):
             print(f"✅ Predicted as Premiere! (Error: {str(e)[:50]}...)")
             return True
        print(f"❌ Not Premiere (VideoUnavailable: {e})")
        return False
    except Exception as e:
        # In the log (Step 343), the error was "Could not retrieve a transcript ... Premieres in ..."
        # checking if that error comes through here.
        if "Premieres in" in str(e):
             print(f"✅ Predicted as Premiere! (Error: {str(e)[:50]}...)")
             return True
        print(f"❌ Not Premiere (Other Error: {e})")
        return False

# The two videos user asked about
videos = [
    "VSdV-AdSlis", # Okta Identity for AI Agents
    "mwzk2rlwtZE"  # Build a Real-Time AI Sales Agent
]

print("--- Testing Premiere Logic ---")
for v in videos:
    is_premiere(v)
