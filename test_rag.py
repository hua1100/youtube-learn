import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 1. Create dummy file
with open("test_rag_doc.txt", "w") as f:
    f.write("The secret code is 123456. The project name is Project Alpha.")

print("1. File created.")

# 2. Upload to File Search Store
try:
    print("2. Creating store...")
    file_search_store = client.file_search_stores.create(
        config={'display_name': "test_store_001"}
    )
    print(f"Store created: {file_search_store.name}")

    print("3. Uploading file...")
    operation = client.file_search_stores.upload_to_file_search_store(
        file="test_rag_doc.txt",
        file_search_store_name=file_search_store.name,
        config={'display_name': "test_doc"}
    )

    while not operation.done:
        print("Waiting for upload...")
        time.sleep(2)
        operation = client.operations.get(operation)

    print("Upload done.")

    # 3. Chat
    print("4. Testing Chat...")
    model = "gemini-2.0-flash"
    prompt = "What is the secret code?"
    
    print(f"Using model: {model}")
    print(f"Store: {file_search_store.name}")

    tool = types.Tool(
        file_search=types.FileSearch(
            file_search_store_names=[file_search_store.name]
        )
    )

    # Try non-streaming first
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[tool]
            )
        )
        print("Response (Non-Stream):", response.text)
    except Exception as e:
        print(f"Error (Non-Stream): {e}")

    # Try streaming
    try:
        stream = client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[tool]
            )
        )
        print("Response (Stream): ", end="")
        for chunk in stream:
            if chunk.text:
                print(chunk.text, end="")
        print("\nStream done.")
    except Exception as e:
        print(f"Error (Stream): {e}")

    # Cleanup
    # client.file_search_stores.delete(name=file_search_store.name, config={'force': True})

except Exception as e:
    print(f"Fatal Error: {e}")
