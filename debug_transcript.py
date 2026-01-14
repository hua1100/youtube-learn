from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print(f"Type: {type(YouTubeTranscriptApi)}")
print(f"Dir: {dir(YouTubeTranscriptApi)}")

try:
    print(f"get_transcript: {YouTubeTranscriptApi.get_transcript}")
except AttributeError as e:
    print(f"Error accessing get_transcript: {e}")

# Try to fetch one transcript
try:
    # Test video: OpenAI + Temporalio
    vid = "k8cnVCMYmNc" 
    t = YouTubeTranscriptApi.get_transcript(vid)
    print("Success fetching transcript!")
except Exception as e:
    print(f"Failed to fetch: {e}")
