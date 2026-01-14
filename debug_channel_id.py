import requests
import re

def get_channel_id_from_url(url):
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        patterns = [
            r'itemprop="channelId" content="([^"]+)"',
            r'"channelId":"([^"]+)"',
            r'"externalId":"([^"]+)"',
            r'"browseId":"(UC[^"]+)"',
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, response.text)
            if matches:
                print(f"Pattern {i} ({pattern}) found: {matches[:3]}...") # Print first 3 matches
    except Exception as e:
        print(f"Error: {e}")

get_channel_id_from_url("https://www.youtube.com/@ycombinator")
