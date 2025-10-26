import logging, requests
import os

# Ver el tema de que, al ejecutar un request de un endpoint, este no esté llamando al publish y que no se ejecute un loop infinito


def handle(event_name, payload, API_BASE_URL, headers):
    data = payload.get("payload", {})
    
    logging.info(f"Procesando evento de usuario: {event_name} con payload {payload} y datos {data}")
    
    user_role = data.get("role", "usuario").lower()
    
    if event_name == "user_created":
        logging.info(f"Alta de {user_role} recibida")
        logging.info("headers: ", headers)
        match user_role:
            case "cliente":
                pass
            case "administrador":
                admin_body = {
                    "nombre": data.get("firstName"),
                    "apellido": data.get("lastName"),
                    "email": data.get("email"),
                    "password": data.get("password", None),
                    "id_admin": int(data.get("userId")),
                    "activo": data.get("activo", True),
                    "foto": data.get("foto", None)
                }
                response = requests.post(f"{API_BASE_URL}/admins", json=admin_body, headers=headers)
            case "prestador":
                pass
        
        logging.info(f"Respuesta del API al crear {user_role}: {response.status_code} - {response.text}")
        
    elif event_name == "user_updated":
        logging.info("Actualización de usuario") #Ver cómo obtener el id?
        response = requests.patch(f"{API_BASE_URL}/usuarios/{data.get('id')}", json=data, headers=headers)
        logging.info(f"Respuesta del API al actualizar usuario: {response.status_code} - {response.text}")
    elif event_name == "user_rejected":
        logging.info("Baja de usuario")
        response = requests.delete(f"{API_BASE_URL}/usuarios/{data.get('id')}", json=data, headers=headers)
        logging.info(f"Respuesta del API al eliminar usuario: {response.status_code} - {response.text}")
    else:
        logging.info(f"Evento de usuario no manejado: {event_name}")
