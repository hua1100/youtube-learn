import json
import os
import time
import random
from tasks.summarizer import summarize_video, save_summary
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

VIDEOS_FILE = "videos.json"

def get_missing_videos():
    if not os.path.exists(VIDEOS_FILE):
        print(f"❌ 找不到 {VIDEOS_FILE}")
        return []
    
    with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
        videos = json.load(f)
    
    missing = []
    for video in videos:
        video_id = video["id"]
        summary_file = f"summary_{video_id}.md"
        if not os.path.exists(summary_file):
            missing.append(video)
    
    return missing

def main():
    print("🔍 正在掃描缺失摘要的影片...")
    missing_videos = get_missing_videos()
    
    if not missing_videos:
        print("✅ 所有影片皆已擁有摘要。")
        return

    print(f"📋 發現 {len(missing_videos)} 部影片缺失摘要。")
    
    for i, video in enumerate(missing_videos):
        video_id = video["id"]
        video_title = video["title"]
        
        print(f"\n[{i+1}/{len(missing_videos)}] 正在處理: {video_title} ({video_id})")
        
        try:
            content = summarize_video(video_id, video_title)
            if content:
                save_summary(video_id, content)
                print(f"✅ 成功補齊摘要: {video_id}")
            else:
                print(f"❌ 無法為 {video_id} 產生摘要 (可能是 429 或無逐字稿)")
        except Exception as e:
            print(f"💥 處理 {video_id} 時發生意外錯誤: {e}")
        
        # 避免連續請求觸發 429
        if i < len(missing_videos) - 1:
            sleep_time = random.uniform(30, 60)
            print(f"😴 為了避免 Rate Limit，休息 {sleep_time:.1f} 秒...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()
