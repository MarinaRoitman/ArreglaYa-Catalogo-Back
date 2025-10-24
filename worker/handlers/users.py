import logging, requests
import os

# Ver el tema de que, al ejecutar un request de un endpoint, este no esté llamando al publish y que no se ejecute un loop infinito


def handle(event_name, payload, API_BASE_URL, headers):
    data = payload.get("payload", {})
    logging.info(f"Procesando evento de usuario: {event_name} con payload {payload} y datos {data}")
    if event_name == "user_created":
        logging.info("👤 Alta de usuario recibida")
        logging.info("headers: ", headers)
        response = requests.post(f"{API_BASE_URL}/usuarios", json=data, headers=headers)
        logging.info(f"Respuesta del API al crear usuario: {response.status_code} - {response.text}")
    elif event_name == "user_updated":
        logging.info("✏️ Actualización de usuario") #Ver cómo obtener el id?
        response = requests.patch(f"{API_BASE_URL}/usuarios/{data.get('id')}", json=data, headers=headers)
        logging.info(f"Respuesta del API al actualizar usuario: {response.status_code} - {response.text}")
    elif event_name == "user_rejected":
        logging.info("🗑️ Baja de usuario")
        response = requests.delete(f"{API_BASE_URL}/usuarios/{data.get('id')}", json=data, headers=headers)
        logging.info(f"Respuesta del API al eliminar usuario: {response.status_code} - {response.text}")
    else:
        logging.info(f"Evento de usuario no manejado: {event_name}")
