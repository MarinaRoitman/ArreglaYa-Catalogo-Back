import logging
import requests

def handle(event_name, payload, API_BASE_URL, headers):
    """
    Maneja los eventos relacionados con calificaciones (reviews).

    Formato esperado del payload:
    {
        "messageId": "283",
        "timestamp": "2025-10-24T21:53:56+00:00",
        "destination": {
            "topico": "calificacion",
            "evento": "creada" | "actualizada"
        },
        "payload": {
            "calificacion_id": int,
            "solicitud_id": int,
            "prestador_id": int,
            "usuario_id": int,
            "puntuacion": int,
            "comentario": str
        }
    }
    """

    # Extraer partes relevantes del mensaje

    data = payload.get("payload", {})

    if not data:
        logging.warning("⚠️ No se encontró payload con datos de calificación, evento ignorado.")
        return
    
    # === Normalizar claves ===
    # Convertir *_id → id_*

    normalized_data = {}
    for key, value in data.items():
        if key == "solicitud_id":
            # ⚠️ Excluir solicitud_id del payload
            continue
        elif key.endswith("_id"):
            # ej: calificacion_id → id_calificacion
            new_key = f"id_{key[:-3]}"  # elimina '_id' y antepone 'id_'
            normalized_data[new_key] = value
        elif key == "puntuacion":
            new_key = "estrellas"
            normalized_data[new_key] = float(value)
        elif key == "comentario":
            new_key = "descripcion"
            normalized_data[new_key] = value
        else:
            normalized_data[key] = value
    logging.info(f"🔄 Payload normalizado: {normalized_data}")

    # === event_name: Calificación creada ===
    if event_name == "creada":
        logging.info("📝 Nueva calificación creada")
        try:
            response = requests.post(
                f"{API_BASE_URL}/calificaciones",
                json=normalized_data,
                headers=headers,
                timeout=5
            )
            logging.info(f"Respuesta del API al crear calificación: {response.status_code} - {response.text}")
        except Exception as e:
            logging.exception(f"Error al enviar POST de calificación creada: {e}")

    # === event_name: Calificación actualizada ===
    elif event_name == "actualizada":
        logging.info("✏️ Calificación actualizada")
        calificacion_id = data.get("calificacion_id")

        if not calificacion_id:
            logging.warning("⚠️ No se encontró 'calificacion_id' en el payload, no se puede actualizar.")
            return

        try:
            response = requests.patch(
                f"{API_BASE_URL}/calificaciones/{calificacion_id}",
                json=normalized_data,
                headers=headers,
                timeout=5
            )
            logging.info(f"Respuesta del API al actualizar calificación: {response.status_code} - {response.text}")
        except Exception as e:
            logging.exception(f"Error al enviar PATCH de calificación actualizada: {e}")

    # === Cualquier otro evento ===
    else:
        logging.info(f"Evento de calificación no manejado: {event_name} / {event_name}")
