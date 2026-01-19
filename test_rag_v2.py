import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import content_types
from collections.abc import Iterable

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Create dummy file
with open("test_rag_doc.txt", "w") as f:
    f.write("The secret code is 999999. The project name is Project Beta.")

print("1. File created.")

# 2. Upload to File API (Not File Search Store? File Search is specific.)
# File Search via google-generativeai uses `request_options`.
# Actually, `google-generativeai` supports `files` API.

try:
    print("2. Uploading file to Files API...")
    myfile = genai.upload_file("test_rag_doc.txt")
    print(f"{myfile=}")

    # Wait for processing
    while myfile.state.name == "PROCESSING":
        print("Processing...")
        time.sleep(2)
        myfile = genai.get_file(myfile.name)
    
    print(f"File State: {myfile.state.name}")

    if myfile.state.name != "ACTIVE":
        raise Exception("File failed to process")

    # 3. Chat
    print("3. Testing Chat with 'gemini-1.5-flash'...")
    # gemini-2.0-flash experimental is also available as "gemini-2.0-flash-exp"
    model_name = "gemini-2.0-flash" 
    
    # In older SDK, we simply pass the file in the history/context, 
    # OR we use the new `tools='file_search'` if supported?
    # Actually, for 2.0/1.5, we can just pass the file object in the contents [prompt, file].
    # This acts as long-context window (up to 1M/2M tokens). 
    # This is NOT RAG (File Search Store), but it solves the problem for <2M tokens!
    # Does the user specifically want "File Search Store" (RAG) or just "Answer from this file"?
    # The user asked about "Gemini File Search".
    
    # However, for <1M tokens (200k chars is tiny), context caching or just passing the file is superior to RAG.
    # But files uploaded via `genai.upload_file` expire in 48h.
    # File Search Stores last forever. The user might want persistence.
    
    # Let's try to use the ACTUAL File Search capability if `google-generativeai` supports it.
    # It seems `google-generativeai` main usage is Context Caching or Long Context.
    # But wait, `google-genai` (new SDK) is specifically for the v1beta API which has File Search Stores.
    
    # Result: If I can't get `google-genai` to work, I should just use `google-generativeai` and context stuffing (passing the file handle).
    # It's robust, supports 1M tokens, and supports streaming.
    # The only downside is 48h expiry, so we'd re-upload if expired.
    
    print("\n--- Trying Context Stuffing (Long Context) ---")
    model = genai.GenerativeModel(model_name)
    
    response = model.generate_content(
        ["What is the secret code?", myfile],
        stream=True
    )
    
    for chunk in response:
        print(chunk.text, end="")
    print("\nDone.")

except Exception as e:
    print(f"Error: {e}")
