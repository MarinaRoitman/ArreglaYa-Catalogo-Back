import logging
import requests

def obtener_id_real(id_secundario,tabla,id_real,url,headers):
    try:
        response = requests.get(
            f"{url}/{tabla}",
            params={id_real:id_secundario},
            headers=headers,
            timeout=5
        )
        # obtener el id real a través del response
        if response.status_code == 200:
            prestador_data = response.json()
            if prestador_data:
                id_encontrado = prestador_data[0].get("id")
                logging.info(f"id obtenido: {id_encontrado}")
        logging.info(f"Respuesta del API: {response.status_code} - {response.text}")
        return id_encontrado
    except Exception as e:
            logging.exception(f"Error al enviar GET de {tabla} {e}")
            return None
    

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
    
    data = payload.get("payload", {})
    prestador_id = data.get("prestador_id")
    usuario_id = data.get("usuario_id")
    
    if not data:
        logging.warning("⚠️ No se encontró payload con datos de calificación, evento ignorado.")
        return
    # obtener id real del prestador
    id_prestador = obtener_id_real(prestador_id,"prestadores","id_prestador",API_BASE_URL,headers)
    
    # obtener id real del usuario
    id_usuario = obtener_id_real(usuario_id,"usuarios","id_usuario",API_BASE_URL,headers)


    # === Normalizar claves ===
        # Crear nuevo body con las claves que espera tu API
    body = {
        "id_calificacion": data.get("calificacion_id"),
        "id_prestador": id_prestador,
        "id_usuario": id_usuario,
        "estrellas": float(data.get("puntuacion", 0)),
        "descripcion": data.get("comentario"),
    }
    logging.info(f"🔄 Payload normalizado: {body}")

    # === event_name: Calificación creada ===
    if event_name == "creada":
        logging.info("📝 Nueva calificación creada")
        try:
            response = requests.post(
                f"{API_BASE_URL}/calificaciones",
                json=body,
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
        id_calificacion = None
        try:
            response = requests.get(
                f"{API_BASE_URL}/calificaciones",
                params={"id_calificacion": calificacion_id},
                headers=headers,
                timeout=5
            )
            # obtener el id real a través del response
            if response.status_code == 200:
                calificacion_data = response.json()
                if calificacion_data:
                    logging.info(f"Calificación obtenida: {calificacion_data}")
                    id_calificacion = calificacion_data[0].get("id") #chequear si hace falta el [0]
            logging.info(f"Respuesta del API al obtener calificación: {response.status_code} - {response.text}")
        except Exception as e:
            logging.exception(f"Error al enviar GET de calificación actualizada: {e}")

        if not id_calificacion:
            logging.warning("⚠️ No se encontró 'calificacion_id' en el payload, no se puede actualizar.")
            return


        try:
            response = requests.patch(
                f"{API_BASE_URL}/calificaciones/{id_calificacion}",
                json=body,
                headers=headers,
                timeout=5
            )
            logging.info(f"Respuesta del API al actualizar calificación: {response.status_code} - {response.text}")
        except Exception as e:
            logging.exception(f"Error al enviar PATCH de calificación actualizada: {e}")

    # === Cualquier otro evento ===
    else:
        logging.info(f"Evento de calificación no manejado: {event_name} / {event_name}")
