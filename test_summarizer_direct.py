from tasks.summarizer import get_transcript_text
import sys
import os

# Fix path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

vid = "k8cnVCMYmNc"
print(f"Testing transcript fetch for {vid}...")
text = get_transcript_text(vid)

if text:
    print(f"✅ Success! Got text length: {len(text)}")
    print(f"Preview: {text[:100]}...")
else:
    print("❌ Failed to get text.")
