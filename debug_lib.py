from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("Dir:", dir(YouTubeTranscriptApi))
try:
    print("get_transcript:", YouTubeTranscriptApi.get_transcript)
except AttributeError:
    print("get_transcript not found")
