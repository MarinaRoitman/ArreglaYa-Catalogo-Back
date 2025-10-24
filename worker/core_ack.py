import os, requests, logging

CORE_ACK_URL = "https://nonprodapi.uade-corehub.com/messages/ack/{subscription_id}"
CORE_API_KEY = os.getenv("CORE_API_KEY")

def send_ack(msg_id, subscription_id):
    if not subscription_id:
        logging.warning(f"No hay subscription_id para {msg_id}, omitiendo ACK.")
        return

    url = CORE_ACK_URL.format(msgId=msg_id)
    payload = {"msgId": msg_id, "subscriptionId": subscription_id}
    headers = {"X-API-KEY": CORE_API_KEY, "Content-Type": "application/json"}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=5)
        r.raise_for_status()
        logging.info(f"ACK enviado correctamente para {msg_id}")
    except Exception as e:
        logging.warning(f"Fallo al enviar ACK para {msg_id}: {e}")
