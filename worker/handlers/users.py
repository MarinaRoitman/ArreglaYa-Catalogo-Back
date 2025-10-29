import logging
import requests
import os

# Ver el tema de que, al ejecutar un request de un endpoint, este no esté llamando al publish y que no se ejecute un loop infinito

def find_user_by_external_id(external_id: int, api_base_url: str, headers: dict):    
    # Probar en /usuarios
    try:
        params = {"id_usuario": external_id}
        get_res = requests.get(f"{api_base_url}/usuarios", params=params, headers=headers)
        if get_res.status_code == 200:
            user_list = get_res.json()
            if user_list and len(user_list) > 0:
                internal_id = user_list[0].get("id")
                if internal_id:
                    logging.info(f"ID Externo {external_id} encontrado en /usuarios (Cliente)")
                    return {"role": "cliente", "internal_id": internal_id, "api_path": "/usuarios"}
    except Exception as e:
        logging.error(f"Error al buscar en /usuarios: {e}")

    # Probar en /prestadores
    try:
        # Tu endpoint GET /prestadores SÍ tiene este filtro
        params = {"id_prestador": external_id}
        get_res = requests.get(f"{api_base_url}/prestadores", params=params, headers=headers)
        if get_res.status_code == 200:
            user_list = get_res.json()
            if user_list and len(user_list) > 0:
                internal_id = user_list[0].get("id")
                if internal_id:
                    logging.info(f"ID Externo {external_id} encontrado en /prestadores")
                    return {"role": "prestador", "internal_id": internal_id, "api_path": "/prestadores"}
    except Exception as e:
        logging.error(f"Error al buscar en /prestadores: {e}")

    # Probar en /admins
    try:
        params = {"id_admin": external_id}
        get_res = requests.get(f"{api_base_url}/admins", params=params, headers=headers)
        if get_res.status_code == 200:
            user_list = get_res.json()
            if user_list and len(user_list) > 0:
                internal_id = user_list[0].get("id")
                if internal_id:
                    logging.info(f"ID Externo {external_id} encontrado en /admins")
                    return {"role": "admin", "internal_id": internal_id, "api_path": "/admins"}
    except Exception as e:
        logging.error(f"Error al buscar en /admins: {e}")
        
    logging.warning(f"ID Externo {external_id} no fue encontrado en ninguna tabla.")
    return None

def handle(event_name, payload, API_BASE_URL, headers):
    data = payload.get("payload", {})
    
    logging.info(f"Procesando evento de usuario: {event_name} con payload {payload} y datos {data}")
    
    user_role = data.get("role", "usuario").lower()
    
    if event_name == "user_created":
        logging.info(f"Alta de {user_role} recibida")
        logging.info(f"headers: {headers}")
        response = None
        user_id_str = data.get("userId")
        user_id_int = None
        if user_id_str:
            try:
                user_id_int = int(user_id_str)
            except ValueError:
                logging.error(f"Error: userId '{user_id_str}' no es un entero. No se puede crear usuario.")
                return

        if not user_id_int:
             logging.error("Error: user_created recibido sin userId válido.")
             return

        match user_role:
            case "cliente":
                addresses = data.get("addresses", [])
                
                addr_pri = addresses[0] if len(addresses) > 0 else {}
                addr_sec = addresses[1] if len(addresses) > 1 else {}

                cliente_body = {
                    "nombre" : data.get("firstName"), 
                    "apellido": data.get("lastName"), 
                    "dni": data.get("dni"), 
                    "telefono": data.get("phoneNumber"), 
                    "id_usuario": user_id_int,
                    
                    "estado_pri": addr_pri.get("state"), 
                    "ciudad_pri":  addr_pri.get("city"), 
                    "calle_pri":  addr_pri.get("street"), 
                    "numero_pri":  addr_pri.get("number"), 
                    "piso_pri":  addr_pri.get("floor"), 
                    "departamento_pri" : addr_pri.get("apartment"),
                    
                    "estado_sec": addr_sec.get("state"), 
                    "ciudad_sec": addr_sec.get("city"), 
                    "calle_sec": addr_sec.get("street"), 
                    "numero_sec": addr_sec.get("number"), 
                    "piso_sec": addr_sec.get("floor"), 
                    "departamento_sec": addr_sec.get("apartment")
                }
                
                response = requests.post(f"{API_BASE_URL}/usuarios", json=cliente_body, headers=headers)
            
            case "admin":
                admin_body = {
                    "nombre": data.get("firstName"),
                    "apellido": data.get("lastName"),
                    "email": data.get("email"),
                    "password": data.get("password", None),
                    "id_admin": user_id_int,
                    "activo": data.get("activo", True),
                    "foto": data.get("foto", None)
                }
                response = requests.post(f"{API_BASE_URL}/admins", json=admin_body, headers=headers)
            
            case "prestador":
                addresses = data.get("addresses", [])
                
                addr = addresses[0] if len(addresses) > 0 else {}
                
                prestador_body = {
                    "nombre": data.get("firstName"),
                    "apellido": data.get("lastName"),
                    "email": data.get("email"),
                    "password": data.get("password", None),
                    "telefono": data.get("phoneNumber"),
                    "dni": data.get("dni"),
                    "foto": data.get("foto", None),
                    "estado": addr.get("state"),
                    "ciudad": addr.get("city"),
                    "calle": addr.get("street"),
                    "numero": addr.get("number"),
                    "piso": addr.get("floor"),
                    "departamento": addr.get("apartment"),
                    
                    "id_prestador": user_id_int
                }
                response = requests.post(f"{API_BASE_URL}/prestadores", json=prestador_body, headers=headers)
        
        if response is not None:
            logging.info(f"Respuesta del API al crear {user_role}: {response.status_code} - {response.text}")
            if response.status_code >= 400:
                 logging.error(f"Error DETALLADO al crear {user_role}: {response.text}")
        else:
            logging.info(f"No se llamó a la API para {user_role}")

    elif event_name == "user_updated":
        logging.info("Update de usuario recibida (rol desconocido)")
        logging.info(f"headers: {headers}")
        
        user_id_str = data.get("userId")
        if not user_id_str:
            logging.error("Evento 'user_updated' recibido sin 'userId'.")
            return
        try:
            user_id_int = int(user_id_str)
        except ValueError:
            logging.error(f"Error: userId '{user_id_str}' no es un entero. No se puede actualizar.")
            return

        user_info = find_user_by_external_id(user_id_int, API_BASE_URL, headers)
        
        if user_info is None:
            logging.error(f"Usuario con id_externo {user_id_int} no encontrado. No se puede actualizar.")
            return
        
        role = user_info["role"]
        internal_id = user_info["internal_id"]
        api_path = user_info["api_path"]
        
        patch_body = {}
        response = None
        
        match role:
            case "cliente":
                field_map = {
                    "firstName": "nombre",
                    "lastName": "apellido",
                    "dni": "dni",
                    "phoneNumber": "telefono",
                    "foto": "foto" 
                }
                for event_key, api_key in field_map.items():
                    if event_key in data:
                        patch_body[api_key] = data[event_key]
                
                if "addresses" in data and isinstance(data.get("addresses"), list):
                    if len(data["addresses"]) > 0:
                        addr_pri = data["addresses"][0]
                        patch_body.update({
                            "estado_pri": addr_pri.get("state"),
                            "ciudad_pri": addr_pri.get("city"),
                            "calle_pri": addr_pri.get("street"),
                            "numero_pri": addr_pri.get("number"),
                            "piso_pri": addr_pri.get("floor"),
                            "departamento_pri": addr_pri.get("apartment")
                        })
                    if len(data["addresses"]) > 1:
                        addr_sec = data["addresses"][1]
                        patch_body.update({
                            "estado_sec": addr_sec.get("state"),
                            "ciudad_sec": addr_sec.get("city"),
                            "calle_sec": addr_sec.get("street"),
                            "numero_sec": addr_sec.get("number"),
                            "piso_sec": addr_sec.get("floor"),
                            "departamento_sec": addr_sec.get("apartment")
                        })
                
                response = requests.patch(f"{API_BASE_URL}{api_path}/{internal_id}", json=patch_body, headers=headers)

            case "admin":
                field_map = {
                    "firstName": "nombre",
                    "lastName": "apellido",
                    "email": "email",
                    "password": "password",
                    "foto": "foto"
                }
                for event_key, api_key in field_map.items():
                    if event_key in data:
                        patch_body[api_key] = data[event_key]
                
                response = requests.patch(f"{API_BASE_URL}{api_path}/{internal_id}", json=patch_body, headers=headers)
            case "prestador":
                field_map = {
                    "firstName": "nombre",
                    "lastName": "apellido",
                    "email": "email",
                    "phoneNumber": "telefono",
                    "password": "contrasena",
                    "dni": "dni",
                    "foto": "foto"
                }
                for event_key, api_key in field_map.items():
                    if event_key in data:
                        patch_body[api_key] = data[event_key]

                # Mapeo de dirección (prestador solo tiene 1)
                address_list = data.get("addresses", [])
                if isinstance(address_list, list) and len(address_list) > 0:
                    addr = address_list[0]
                    # Solo actualizar si el diccionario addr no está vacío
                    if addr:
                        patch_body.update({
                            "estado": addr.get("state"),
                            "ciudad": addr.get("city"),
                            "calle": addr.get("street"),
                            "numero": addr.get("number"),
                            "piso": addr.get("floor"),
                            "departamento": addr.get("apartment")
                        })
                
                response = requests.patch(f"{API_BASE_URL}{api_path}/{internal_id}", json=patch_body, headers=headers)
        
        if response is not None:
            logging.info(f"Respuesta del API al actualizar {user_role}: {response.status_code} - {response.text}")
            if response.status_code >= 400:
                 logging.error(f"Error DETALLADO al actualizar {user_role}: {response.text}")
        else:
            logging.info(f"No se llamó a la API para {user_role}")
    
    elif event_name == "user_rejected":
        logging.info(f"rejected de {user_role} recibida")
        logging.info(f"headers: {headers}")
        response = None
        match user_role:
            case "cliente":
                pass
            case "admin":
                pass
            case "prestador":
                pass
                # Aca habría que hacer algo? Supongo que no
        if response is not None:
            logging.info(f"Respuesta del API al rechazar {user_role}: {response.status_code} - {response.text}")
        else:
            logging.info(f"No se llamó a la API")

    elif event_name == "user_deactivated":
        logging.info("Deactivate de usuario recibida (rol desconocido)")
        logging.info(f"headers: {headers}")
        response = None
        
        user_id_str = data.get("userId")
        if not user_id_str:
            logging.error("Evento 'user_deactivated' recibido sin 'userId'.")
            return

        try:
            user_id_int = int(user_id_str)
        except ValueError:
            logging.error(f"Error: userId '{user_id_str}' no es un entero. No se puede desactivar.")
            return
        
        user_info = find_user_by_external_id(user_id_int, API_BASE_URL, headers)

        if user_info is None:
            logging.error(f"Usuario con id_externo {user_id_int} no encontrado. No se puede desactivar.")
            return

        role = user_info["role"]
        internal_id = user_info["internal_id"]
        api_path = user_info["api_path"]

        logging.info(f"Usuario encontrado. Rol: {role}, ID Interno: {internal_id}. Procediendo a desactivar (DELETE).")
        
        delete_url = f"{API_BASE_URL}{api_path}/{internal_id}"
        logging.info(f"Enviando DELETE para rol '{role}' a {delete_url}")
        try:
            response = requests.delete(delete_url, headers=headers)
            response.raise_for_status()
            logging.info(f"Usuario {role} con ID interno {internal_id} desactivado correctamente.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error en DELETE a {delete_url}: {e}")

        if response is not None:
            logging.info(f"Respuesta del API al desactivar {role}: {response.status_code} - {response.text if response.text else '(No body)'}")
        else:
             logging.warning(f"No se pudo completar la llamada DELETE para {role} {internal_id} o ya estaba loggeado el error.")
        
        if response is not None:
            logging.info(f"Respuesta del API al desactivar {user_role}: {response.status_code} - {response.text}")
        else:
            logging.info(f"No se llamó a la API")
    else:
        logging.info(f"Evento de usuario no manejado: {event_name}")