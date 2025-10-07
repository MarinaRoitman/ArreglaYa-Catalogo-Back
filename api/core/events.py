import json
import requests

def publish_event(messageId, timestamp, channel, eventName, payload):
    url = "https://nonprodapi.uade-corehub.com/publish"
    headers = {
        "X-API-KEY": "ch_812ec720cd32409693886474bda08640",
        "Content-Type": "application/json"
    }
    # Timestamp must be ISO-8601 UTC
    body = {
        "messageId": messageId,
        "timestamp": timestamp,
        "source": "catalogue",
        "destination": {
            "channel": channel,
            "eventName": eventName
        },
        "payload": payload
    }
    
    """print(f"➡️ URL: {url}")
    print(f"➡️ Headers: {headers}")
    print(f"➡️ Body JSON:\n{json.dumps(body, indent=4, ensure_ascii=False)}")
        
    response = requests.post(url, headers=headers, json=body)
    
    print(f"Respuesta del corehub====")
    print(f"⬅️ Código HTTP: {response.status_code}")
    print(f"⬅️ Texto completo:\n{response.text}")
    try:
        response_data = response.json() if response.text else {}
    except ValueError:
        response_data = {}"""