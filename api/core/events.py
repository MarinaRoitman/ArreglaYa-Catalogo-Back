
import json
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

CORE_URL = "https://nonprodapi.uade-corehub.com/publish"
CORE_API_KEY = os.getenv("CORE_API_KEY")

def publish_event(message_id: str, timestamp: str, topic: str, event_name: str, payload: dict):
    """
    Publica un evento al Core Hub con el nuevo formato (topic + eventName).
    """
    headers = {
        "X-API-KEY": CORE_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "messageId": message_id,
        "timestamp": timestamp,
        "destination": {
            "topic": topic,
            "eventName": event_name
        },
        "payload": payload
    }

    response = requests.post(CORE_URL, headers=headers, json=body)

    # Log opcional (para debugging local)
    # print(f"➡️ Evento publicado al Core ({response.status_code})")
    # print(json.dumps(body, indent=4, ensure_ascii=False))
    # if response.status_code != 200:
    #    print(f"❌ Error: {response.text}")

    return response
