from youtube_transcript_api import YouTubeTranscriptApi

try:
    print("Attempting to fetch transcript with new API...")
    yt = YouTubeTranscriptApi()
    vid = "k8cnVCMYmNc"
    
    t = yt.fetch(vid, languages=['zh-TW', 'zh', 'en'])
    
    print(f"Result type: {type(t)}")
    print(f"Result dir: {dir(t)}")
    
    # Try converting to list?
    try:
        data = list(t)
        print(f"Converted to list, len: {len(data)}")
        if len(data) > 0:
            print(f"First item: {data[0]}")
    except:
        print("Not iterable")

except Exception as e:
    print(f"Error: {e}")
