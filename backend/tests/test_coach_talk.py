import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import time

def generate_talk(text, avatar_id):
    load_dotenv()
    api_key = os.environ.get("DID_API_KEY")
    if not api_key or ":" not in api_key:
        raise ValueError("DID_API_KEY is not set correctly or missing ':'")
    username, password = api_key.split(":", 1)

    data = {
        "script": {
            "type": "text",
            "input": text
        },
        "source_url": f"https://d-id-talks-prod.s3.us-west-2.amazonaws.com/api~talks~{avatar_id}/image.jpg"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    print("🔄 Sending POST to /talks ...")
    response = requests.post(
        "https://api.d-id.com/talks",
        auth=HTTPBasicAuth(username, password),
        headers=headers,
        json=data
    )

    if response.status_code != 201:
        print("❌ Error creating talk:", response.status_code, response.text)
        return

    talk_id = response.json()["id"]
    print(f"✅ Talk created with ID: {talk_id}")

    status_url = f"https://api.d-id.com/talks/{talk_id}"
    while True:
        time.sleep(2)
        status_response = requests.get(status_url, auth=HTTPBasicAuth(username, password))
        status_data = status_response.json()

        status = status_data.get("status")
        print(f"⏳ Status: {status}")

        if status == "done":
            video_url = status_data["result_url"]
            print(f"✅ Video ready! Downloading from: {video_url}")

            video_data = requests.get(video_url).content
            with open("coach_dynamic_output.mp4", "wb") as f:
                f.write(video_data)
            print("🎬 Video saved as coach_dynamic_output.mp4")
            break

        elif status == "error":
            print("❌ Error during generation:", status_data.get("error", "Unknown error"))
            break

if __name__ == "__main__":
    # Change this text to test different inputs
    test_text = "Hej! Jag är din nya AI-coach. Vad vill du veta om matchen?"
    avatar_id = "tlk_wTHnOKslS2E4R14_sMcoo"
    generate_talk(test_text, avatar_id)
