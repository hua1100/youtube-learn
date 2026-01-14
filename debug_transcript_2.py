import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("--- Module Dir ---")
print(dir(youtube_transcript_api))

print("\n--- Class Dir ---")
print(dir(YouTubeTranscriptApi))

print("\n--- Class Help ---")
try:
    help(YouTubeTranscriptApi)
except:
    pass
