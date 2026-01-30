import json
from datetime import datetime
import dateutil.parser

file_path = "videos.json"

def parse_date(date_str):
    try:
        # Use dateutil for robust parsing (handles ISO, RFC, etc.)
        # Ensure it's timezone-aware if possible, or naive if not
        dt = dateutil.parser.parse(date_str)
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            dt = dt.replace(tzinfo=dateutil.tz.tzutc())
        return dt
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return datetime.min.replace(tzinfo=dateutil.tz.tzutc())

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Sort descending by published date
    data.sort(key=lambda x: parse_date(x.get('published', '')), reverse=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully sorted {len(data)} videos by date.")

except Exception as e:
    print(f"Failed to sort videos: {e}")
