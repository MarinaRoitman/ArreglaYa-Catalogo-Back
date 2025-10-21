import logging, requests
from os import getenv

ADMIN_TOKEN = getenv("ADMIN_TOKEN") # se debe reemplazar cada vez que vence

# Ver el tema de que, al ejecutar un request de un endpoint, este no esté llamando al publish y que no se ejecute un loop infinito


headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }

def handle(event_name, payload, API_BASE_URL):
    data = payload.get("payload", {})
    logging.info(f"Procesando evento de usuario: {event_name} con payload {payload} y datos {data}")
    if event_name == "user_created":
        logging.info("👤 Alta de usuario recibida")
        requests.post(f"{API_BASE_URL}/usuarios", json=data, headers=headers) # modificar para que apunte a la url correcta (local o prod)
    elif event_name == "user_updated":
        logging.info("✏️ Actualización de usuario")
        requests.patch(f"{API_BASE_URL}/usuarios", json=data, headers=headers)
    elif event_name == "user_rejected":
        logging.info("🗑️ Baja de usuario")
        requests.delete(f"{API_BASE_URL}/usuarios", json=data, headers=headers)
    else:
        logging.info(f"Evento de usuario no manejado: {event_name}")
