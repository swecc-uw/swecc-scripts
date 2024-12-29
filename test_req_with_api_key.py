import os
import requests
import json
"""
Use me to test your api key
"""
if __name__ == "__main__":
    swecc_url = os.getenv('SWECC_URL')
    api_key = os.getenv('SWECC_API_KEY')

    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json",
    }

    url = f"{swecc_url}/engagement/message/"
    data = {
        "channel_id": 1,
        "discord_id": 1,
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 202:
        try:
            print("Error Response:", response.json())
        except json.JSONDecodeError:
            print("Raw Error Response:", response.text)