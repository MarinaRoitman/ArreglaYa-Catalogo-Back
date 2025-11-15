import os
import requests
import logging

CORE_ACK_URL = "https://nonprodapi.uade-corehub.com/messages/ack/{subscriptionId}"
CORE_API_KEY = os.getenv("CORE_API_KEY")

def send_ack(message_id, subscription_id):
    if not subscription_id:
        logging.warning(f"No hay subscription_id para {message_id}, omitiendo ACK.")
        return

    # URL correcta reemplazando subscriptionId
    url = CORE_ACK_URL.format(subscriptionId=subscription_id)

    payload = {"messageId": message_id}
    headers = {
        "X-API-KEY": CORE_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        r.raise_for_status()
        logging.info(f"ACK enviado correctamente para {message_id}")
    except Exception as e:
        logging.warning(f"Fallo al enviar ACK para {message_id}: {e}")
