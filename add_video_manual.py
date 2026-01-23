import sys
import os
import re
import json
import requests
from datetime import datetime

# 將專案根目錄加入 sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from tasks.monitor_task import update_video_db
from tasks.summarizer import summarize_video, save_summary

def get_video_id(url):
    """提取 YouTube Video ID"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_video_info(video_id):
    """獲取影片資訊 (標題與頻道)"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        # 使用簡單的爬蟲獲取標題，或者如果環境有 yt-dlp 就更好
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        
        # 提取標題
        title_match = re.search(r'<title>(.*?) - YouTube</title>', response.text)
        title = title_match.group(1) if title_match else f"Video {video_id}"
        
        # 提取頻道名稱 (簡化版)
        channel_match = re.search(r'"author":"(.*?)"', response.text)
        channel_title = channel_match.group(1) if channel_match else "Unknown Channel"
        
        return {
            'id': video_id,
            'title': title,
            'link': url,
            'published': datetime.now().isoformat(),
            'channel_title': channel_title
        }
    except Exception as e:
        print(f"⚠️ 獲取影片資訊失敗: {e}")
        return {
            'id': video_id,
            'title': f"Manual Added Video {video_id}",
            'link': url,
            'published': datetime.now().isoformat(),
            'channel_title': "Manual Add"
        }

def main():
    if len(sys.argv) < 2:
        print("用法: python add_video_manual.py <YouTube_URL_或_ID>")
        sys.exit(1)
        
    input_str = sys.argv[1]
    video_id = get_video_id(input_str) if "youtube.com" in input_str or "youtu.be" in input_str else input_str
    
    if not video_id or len(video_id) != 11:
        print(f"❌ 無效的 Video ID 或 URL: {input_str}")
        sys.exit(1)
        
    print(f"🚀 開始處理影片: {video_id}")
    
    # 1. 獲取基本資訊
    video_info = get_video_info(video_id)
    print(f"✅ 標題: {video_info['title']}")
    print(f"✅ 頻道: {video_info['channel_title']}")
    
    # 2. 生成摘要
    summary_content = summarize_video(video_id, video_info['title'])
    if summary_content:
        save_summary(video_id, summary_content)
        video_info['has_summary'] = True
    else:
        print("⚠️ 摘要生成失敗，但仍將影片加入資料庫。")
        video_info['has_summary'] = False
        
    # 3. 更新資料庫
    update_video_db(video_info)
    print(f"\n✨ 任務完成！影片 「{video_info['title']}」 已新增。")

if __name__ == "__main__":
    main()
