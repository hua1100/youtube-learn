import json
import os
import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
import os

# 將專案根目錄加入 sys.path，以便能找到 tasks 模組
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasks.summarizer import summarize_video, save_summary
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable

STATE_FILE = "monitor_state.json"
OUTPUT_FILE = "new_videos.txt"

CHANNELS = [
    "https://www.youtube.com/@LennysPodcast",
    "https://www.youtube.com/@googleantigravity",
    "https://www.youtube.com/@Google/videos",
    "https://www.youtube.com/@ycombinator",
    "https://www.youtube.com/@a16z",
    "https://www.youtube.com/@aiDotEngineer",
    "https://www.youtube.com/@EveryInc",
    "https://www.youtube.com/@AcquiredFM",
    "https://www.youtube.com/@howiaipodcast",
    "https://www.youtube.com/@hamelhusain7140",
    "https://www.youtube.com/@StephenGPope"
]

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_channel_id_from_url(url):
    """
    從 YouTube 頻道 URL 提取 Channel ID。
    """
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        patterns = [
            r'"externalId":"([^"]+)"',
            r'"browseId":"(UC[^"]+)"',
            r'itemprop="channelId" content="([^"]+)"',
            r'"channelId":"([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
            
        print(f"⚠️ 無法從 {url} 提取 Channel ID")
        return None
    except Exception as e:
        print(f"❌ 獲取 {url} 時發生錯誤: {e}")
        return None

def is_shorts(video_id):
    """
    Check if a video is a YouTube Short by requesting the /shorts/ endpoint.
    If it's a Short, it returns 200.
    If it's a regular video, it redirects (303) to /watch.
    """
    url = f"https://www.youtube.com/shorts/{video_id}"
    try:
        # allow_redirects=False to catch the 303 redirect
        resp = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=False, timeout=5)
        if resp.status_code == 200:
            return True
        elif resp.status_code == 303:
            return False
        else:
            # Ambiguous case, assume False or check handling
            return False
    except:
        return False

def is_premiere(video_id):
    """
    Check if a video is a Premiere (not yet available).
    Relies on YouTubeTranscriptApi throwing a specific error for premieres.
    """
    try:
        # Just try to fetch transcripts.
        yt_api = YouTubeTranscriptApi()
        yt_api.fetch(video_id, languages=['en']) # Language doesn't matter for checking availability
        return False
    except VideoUnavailable as e:
        if "Premieres in" in str(e):
             return True
        return False
    except Exception as e:
        # Check string for generic exceptions too, as seen in tests
        if "Premieres in" in str(e):
            return True
        # Other errors (e.g. no transcripts but video exists) are not "Premiere" state
        return False

def get_new_videos(channel_id, last_video_link=None):
    """
    使用 RSS Feed 獲取「新」影片列表。
    如果提供了 last_video_link，回傳該連結之後的所有影片。
    如果沒提供 (Init)，只回傳最新的一部。
    """
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        response = requests.get(rss_url, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        
        found_videos = []

        # Iterate through entries
        for entry in root.findall('atom:entry', ns):
            video_id_elem = entry.find('yt:videoId', ns)
            video_id = video_id_elem.text if video_id_elem is not None else None
            
            if not video_id:
                continue

            link = entry.find('atom:link', ns).attrib['href']
            
            # 1. Check stop condition (Hit previous video)
            if last_video_link and link == last_video_link:
                break
                
            # 2. Check Shorts
            if is_shorts(video_id):
                print(f"⚠️ 跳過 Shorts: {video_id}")
                continue

            # 3. Check Premiere
            if is_premiere(video_id):
                print(f"⏳ 影片尚在首播預告中，跳過: {video_id}")
                continue

            title = entry.find('atom:title', ns).text
            published = entry.find('atom:published', ns).text
            
            # Extract Channel Title
            channel_title = "Unknown"
            author = entry.find('atom:author', ns)
            if author is not None:
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    channel_title = name_elem.text

            video_info = {
                'id': video_id,
                'title': title,
                'link': link,
                'published': published,
                'channel_title': channel_title
            }
            
            found_videos.append(video_info)
            
            # 3. If Init mode (no last_video_link), we only want the LATEST single healthy video
            if last_video_link is None:
                break
                
        return found_videos
        
    except Exception as e:
        print(f"❌ 獲取 RSS {channel_id} 時發生錯誤: {e}")
        return []

def update_video_db(video_info):
    """
    Helper function to update videos.json with a single video immediately.
    """
    history_file = "videos.json"
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass
    
    # Check if exists
    for v in history:
        if v.get('id') == video_info['id']:
            return

    history.insert(0, video_info) # Add to top
    print(f"📚 立即新增影片到資料庫: {video_info['title']}")
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def check_updates():
    """
    定期檢查任務主函數
    """
    print(f"[{datetime.now()}] 開始檢查 YouTube 頻道更新...")
    state = load_state()
    state_updated = False
    new_video_entries = []
    
    for url in CHANNELS:
        print(f"👀 正在檢查: {url}")
        # 如果 state 中沒有緩存 channel_id，則重新獲取
        if url in state and 'channel_id' in state[url]:
            channel_id = state[url]['channel_id']
        else:
            channel_id = get_channel_id_from_url(url)
            if channel_id:
                if url not in state:
                    state[url] = {}
                state[url]['channel_id'] = channel_id
                state_updated = True
        
        if channel_id:
            last_video_link = state.get(url, {}).get('last_video_link')
            
            # Get list of new videos
            new_videos_list = get_new_videos(channel_id, last_video_link)
            
            if new_videos_list:
                print(f"🔎 發現 {len(new_videos_list)} 部新影片 (Channel: {url})")
                
                # Process from Oldest to Newest to maintain chronological order in state/logs
                for video_info in reversed(new_videos_list):
                    current_video_link = video_info['link']
                    
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    entry = f"[{timestamp}] New Video: {video_info['title']} - {video_info['link']}\n"
                    new_video_entries.append(entry)
                    print(entry.strip())
                    
                    # 觸發摘要生成
                    if video_info.get('id'):
                        summary_content = summarize_video(video_info['id'], video_info['title'])
                        if summary_content:
                            save_summary(video_info['id'], summary_content)
                    
                    # === Real-time Update: Save to DB Immediately ===
                    update_video_db(video_info)

                    if url not in state:
                        state[url] = {}
                    state[url]['last_video_link'] = current_video_link
                    state[url]['last_video_title'] = video_info['title']
                    state[url]['last_checked'] = datetime.now().isoformat()
                    # Save state immediately too, to prevent duplicate processing if crash
                    save_state(state) 
                    state_updated = False # Handled above

    # Write log file for record (optional batch write or append)
    if new_video_entries:
        print(f"📝 寫入 {len(new_video_entries)} 筆新影片紀錄到 {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f: # Changed to append mode 'a'
            for entry in new_video_entries:
                f.write(entry)
    else:
        print("沒有發現新影片。")
    
    print(f"[{datetime.now()}] 檢查完成。\n")
    return len(new_video_entries)

if __name__ == "__main__":
    # 用於測試
    check_updates()
