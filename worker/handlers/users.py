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
        response = None
        match user_role:
            case "cliente":
                if len(data.get("address", [])) > 1:
                    cliente_body = {
                        "nombre" : data.get("firstName"), "apellido": data.get("lastName"), "dni": data.get("dni"), "telefono": data.get("phoneNumber"), "id_usuario": data.get("userId"),
                        "estado_pri": data.get("address")[0].get("state"), "ciudad_pri":  data.get("address")[0].get("city"), "calle_pri":  data.get("address")[0].get("street"), "numero_pri":  data.get("address")[0].get("number"), "piso_pri":  data.get("address")[0].get("floor", None), "departamento_pri" :  data.get("address")[0].get("apartment", None),
                        "estado_sec": data.get("address")[1].get("state", None), "ciudad_sec": data.get("address")[1].get("city", None), "calle_sec": data.get("address")[1].get("street", None), "numero_sec": data.get("address")[1].get("number", None), "piso_sec": data.get("address")[1].get("floor", None), "departamento_sec": data.get("address")[1].get("apartment", None)
                    }
                else:
                    cliente_body = {
                        "nombre" : data.get("firstName"), "apellido": data.get("lastName"), "dni": data.get("dni"), "telefono": data.get("phoneNumber"), "id_usuario": data.get("userId"),
                        "estado_pri": data.get("address")[0].get("state"), "ciudad_pri":  data.get("address")[0].get("city"), "calle_pri":  data.get("address")[0].get("street"), "numero_pri":  data.get("address")[0].get("number"), "piso_pri":  data.get("address")[0].get("floor", None), "departamento_pri" :  data.get("address")[0].get("apartment", None),
                    }
                response = requests.post(f"{API_BASE_URL}/usuarios", json=cliente_body, headers=headers)
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
                prestador_body = {
                    "nombre": data.get("firstName"),
                    "apellido": data.get("lastName"),
                    "email": data.get("email"),
                    "password": data.get("password", None),
                    "telefono": data.get("phoneNumber"),
                    "dni": data.get("dni"),
                    "foto": data.get("foto", None),
                    "estado": data.get("address")[0].get("state"),
                    "ciudad": data.get("address")[0].get("city"),
                    "calle": data.get("address")[0].get("street"),
                    "numero": data.get("address")[0].get("number"),
                    "piso": data.get("address")[0].get("floor", None),
                    "departamento": data.get("address")[0].get("apartment", None),
                    "id_prestador": int(data.get("userId"))
                }
                response = requests.post(f"{API_BASE_URL}/prestadores", json=prestador_body, headers=headers)
        if response or response.status_code == 500:
            logging.info(f"Respuesta del API al crear {user_role}: {response.status_code} - {response.text}")
        else:
            logging.info(f"No se llamó a la API / {response}")
    elif event_name == "user_updated":
        logging.info(f"Update de {user_role} recibida")
        logging.info("headers: ", headers)
        response = None
        match user_role:
            case "cliente":
                # cliente_response = requests.get(f"{API_BASE_URL}/usuarios", params={"id_usuario": data.get("userId")}, headers=headers)
                pass
            case "administrador":
                pass
            case "prestador":
                pass
        if response:
            logging.info(f"Respuesta del API al crear {user_role}: {response.status_code} - {response.text}")
        else:
            logging.info(f"No se llamó a la API")
        
    elif event_name == "user_rejected":
        logging.info(f"rejected de {user_role} recibida")
        logging.info("headers: ", headers)
        response = None
        match user_role:
            case "cliente":
                pass
            case "administrador":
                pass
            case "prestador":
                pass
                # Aca habría que hacer algo? Supongo que no
        if response:
            logging.info(f"Respuesta del API al crear {user_role}: {response.status_code} - {response.text}")
        else:
            logging.info(f"No se llamó a la API")
    elif event_name == "user_deactivated":
        logging.info(f"delete de {user_role} recibida")
        logging.info("headers: ", headers)
        response = None
        match user_role:
            case "cliente":
                pass
            case "administrador":
                pass
            case "prestador":
                pass
        if response:
            logging.info(f"Respuesta del API al crear {user_role}: {response.status_code} - {response.text}")
        else:
            logging.info(f"No se llamó a la API")
    else:
        logging.info(f"Evento de usuario no manejado: {event_name}")
