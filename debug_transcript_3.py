from youtube_transcript_api import YouTubeTranscriptApi

try:
    print("Attempting to fetch transcript with new API...")
    yt = YouTubeTranscriptApi()
    # Test video: OpenAI + Temporalio
    vid = "k8cnVCMYmNc"
    
    # Try fetch
    print("Calling fetch()...")
    t = yt.fetch(vid, languages=['zh-TW', 'zh', 'en'])
    
    # Check result
    if t:
        print(f"Success! Got {len(t.fetch())} lines (wait, fetch returns object?)") 
        # Wait, the help said fetch() returns FetchedTranscript. 
        # And FetchedTranscript has .fetch() method? No.
        # Help says: fetch(...) -> FetchedTranscript
        # But wait, looking at help:
        # fetch(...) -> FetchedTranscript
        # And usually we want the list of dicts.
        # Let's see what t is.
        print(f"Result type: {type(t)}")
        print(f"Result dir: {dir(t)}")
        
        # Maybe we need to call something on t?
        # Standard API returns list of dicts.
        
except Exception as e:
    print(f"Error: {e}")
