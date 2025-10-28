import logging, requests

def obtener_id_real(id_secundario,endpoint,id_real,url,headers):
    try:
        response = requests.get(
            f"{url}/{endpoint}",
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
            logging.exception(f"Error al enviar GET de {endpoint} {e}")
            return None
    
