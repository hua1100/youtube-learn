from tasks.summarizer import summarize_video, save_summary

video_id = "2hgjgycOU_0"
video_title = "Inside The Startup Building Reusable Rockets"

print(f"Manually triggering summary for {video_id}...")
content = summarize_video(video_id, video_title)

if content:
    save_summary(video_id, content)
    print("Success!")
else:
    print("Failed.")
