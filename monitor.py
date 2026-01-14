import requests
import re
import xml.etree.ElementTree as ET
from datetime import datetime
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "requests",
# ]
# ///
def get_channel_id_from_url(url):
    """
    從 YouTube 頻道 URL 提取 Channel ID。
    如果是 @Handle URL 或 /channel/ URL，嘗試從頁面內容提取 channel_id。
    """
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # 嘗試多種正則表達式來尋找 Channel ID
        patterns = [
            r'itemprop="channelId" content="([^"]+)"',  # meta tag
            r'"channelId":"([^"]+)"',                    # JSON config
            r'"externalId":"([^"]+)"',                   # JSON config
            r'"browseId":"(UC[^"]+)"',                   # ytInitialData (Channel IDs start with UC)
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
def get_latest_video(channel_id):
    """
    使用 RSS Feed 獲取最新影片資訊 (自動跳過 Shorts)
    """
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        
        # XML Namespace (Atom)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015'}
        
        # 遍歷所有 entries 尋找第一個非 Shorts 的影片
        for entry in root.findall('atom:entry', ns):
            link = entry.find('atom:link', ns).attrib['href']
            
            # 檢查是否為 Shorts
            if '/shorts/' in link:
                continue

            title = entry.find('atom:title', ns).text
            published = entry.find('atom:published', ns).text
            # 簡單格式化時間 (移除時區資訊以便閱讀，或保留)
            # 格式範例: 2025-01-13T12:00:00+00:00
            
            return {
                'title': title,
                'link': link,
                'published': published
            }
        
        return None
    except Exception as e:
        print(f"❌ 獲取 RSS {channel_id} 時發生錯誤: {e}")
        return None
def main():
    channels = [
        "https://www.youtube.com/@LennysPodcast",
        "https://www.youtube.com/@googleantigravity",
        "https://www.youtube.com/@Google/videos",
        "https://www.youtube.com/@ycombinator",
        "https://www.youtube.com/@a16z",
        "https://www.youtube.com/@aiDotEngineer"
    ]
    print(f"開始檢查 {len(channels)} 個頻道...\n")
    for url in channels:
        print(f"正在檢查: {url} ...")
        channel_id = get_channel_id_from_url(url)
        
        if channel_id:
            # print(f"  -> Channel ID: {channel_id}") # Debug usage
            video_info = get_latest_video(channel_id)
            
            if video_info:
                print(f"  ✅ 最新影片: {video_info['title']}")
                print(f"  📅 發布時間: {video_info['published']}")
                print(f"  🔗 連結: {video_info['link']}")
            else:
                print("  ⚠️ 尚無影片或無法解析 RSS")
        
        print("-" * 50)
if __name__ == "__main__":
    main()
