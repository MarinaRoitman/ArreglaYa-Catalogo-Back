
import logging, requests
from handlers.helpers import obtener_id_real

def handle(event_name, payload, api_base_url, headers):
  # COTIZACION CREADA --> testear
  if event_name == "emitida":
    logging.info("📦 Nueva solicitud de cotización emitida")
    payload_data = payload.get("payload", {})

    solicitudes = payload_data.get("solicitudes", [])
    if not solicitudes:
        logging.warning("⚠️ No se encontraron solicitudes en el payload, evento ignorado.")
        return

    total_creados = 0

    for solicitud in solicitudes:
        solicitud_id = solicitud.get("solicitudId")
        descripcion = solicitud.get("descripcion")
        es_critico = solicitud.get("esCritica", False)
        fecha = solicitud.get("timestamp") or payload_data.get("generatedAt")

        # Recorrer los prestadores en top3
        for prestador in solicitud.get("top3", []):
            body = {
                "id_pedido": solicitud_id,
                "descripcion": descripcion or f"Solicitud {solicitud_id}",
                "estado": "pendiente",
                "es_critico": es_critico,
                "fecha": fecha,
                "id_habilidad": prestador.get("habilidadId"),
                "id_prestador": prestador.get("prestadorId"),
                "id_usuario": None,  # No viene en el payload
                "id_zona": None,     # No viene en el payload
                "tarifa": None       # No viene en el payload
            }

            logging.info(f"📝 Creando pedido para prestador {prestador.get('prestadorNombre')} con body: {body}")

            try:
                response = requests.post(
                    f"{api_base_url}/pedidos/",
                    json=body,
                    headers=headers,
                    timeout=5
                )

                if response.status_code == 201:
                    total_creados += 1
                    logging.info(f"✅ Pedido creado correctamente para prestador {prestador.get('prestadorId')}")
                else:
                    logging.warning(f"⚠️ Error creando pedido ({response.status_code}): {response.text}")

            except requests.Timeout:
                logging.error(f"⏰ Timeout al crear pedido para prestador {prestador.get('prestadorId')}")
            except requests.RequestException as e:
                logging.error(f"💥 Error de request al crear pedido: {e}")

    logging.info(f"📊 Total de pedidos creados: {total_creados}")

    # COTIZACION ACEPTADA
    if event_name == "aceptada":
        logging.info("📦 Nueva solicitud de cotización aceptada")
        logging.info (f"Payload recibido: {payload}")
        data = payload.get("payload", {})
        pedido_id = data.get("solicitud_id")

        if not data:
            logging.warning("⚠️ No se encontró payload con datos de pago, evento ignorado.")
            return

      # Normalización del payload
        body = {
            "estado":"aprobado_por_usuario",
            "tarifa": data.get("monto")
        }
        logging.info(f"🔄 Payload normalizado: {body}")


        id_pedido = obtener_id_real(pedido_id,"pedidos","id_pedido",api_base_url,headers)

        # persistir en la tabla pedidos
        try:
            response = requests.patch(
            f"{api_base_url}/pedidos/{id_pedido}",
            json=body,
            timeout=5,
            headers=headers
            )
            logging.info(f"Respuesta del API al actualizar el pedido: {response.status_code} - {response.text}")
            if response.status_code == 200:
              logging.info("✅ Cotización aceptada")
        except requests.Timeout:
            logging.error("⏰ Timeout al crear pedido")
        except requests.RequestException as e:
            logging.error(f"💥 Error al crear pedido: {e}")

    # COTIZACION RECHAZADA (igual que cancelación de pedidos)
    elif event_name == "rechazada":
      logging.info("📦 Nueva solicitud de pedido cancelado")
      logging.info (f"Payload recibido: {payload}")
      data = payload.get("payload", {})
      pedido_id = data.get("solicitud_id")

      if not data:
        logging.warning("⚠️ No se encontró payload con datos de pago, evento ignorado.")
        return

      id_pedido = obtener_id_real(pedido_id,"pedidos","id_pedido",api_base_url,headers)

      try:
          response = requests.delete(
              f"{api_base_url}/pedidos/{id_pedido}",
              timeout=5,
              headers=headers
          )
          logging.info(f"Respuesta del API al cancelar el pedido: {response.status_code} - {response.text}")
      except requests.Timeout:
          logging.error("⏰ Timeout al cancelar pedido")
      except requests.RequestException as e:
          logging.error(f"💥 Error al cancelar pedido: {e}")


        
    

"""

ejemplo aceptada:
{
  "messageId": "2",
  "timestamp": "2025-09-27T14:01:19.663Z",
  "destination": {
    "topic": "cotizacion",
    "eventName": "aceptada"
  },
  "payload": {
    "solicitud_id": 120045,
    "usuario_id": 901,
    "prestador_id": 5552,
    "monto": 72000
  }
}

ejemplo rechazada:

{
  "messageId": "1",
  "timestamp": "2025-09-27T14:00:19.663Z",
  "destination": {
    "topic": "cotizacion",
    "eventName": "rechazada"
  },
  "payload": {
    "cotizacion_id": 774002,
    "solicitud_id": 120045,
    "usuario_id": 901,
    "prestador_id": 5553,
    "comentario": "Me queda alto el presupuesto."
  }
}


cotizacion emitida

{
  "messageId": "90e440da-f3f6-4e14-ba8e-1652d83b4714",
  "timestamp": "2025-10-24T21:57:43.327443Z",
  "destination": {
    "topic": "cotizacion",
    "eventName": "emitida"
  },
  "payload": {
    "generatedAt": "2025-10-24T21:57:43.327198Z",
    "solicitudes": [
      {
        "solicitudId": 1001,
        "descripcion": "Pintar living y pasillo",
        "estado": "COTIZANDO",
        "fueCotizada": true,
        "esCritica": false,
        "top3": [
          {
            "prestadorId": 2,
            "prestadorNombre": "Maria Gomez",
            "mensaje": "Invitación a cotizar 1001",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.293618Z",
            "habilidadId": 4,
            "rubroId": 3,
            "cotizacionId": null,
            "solicitudId": 1001
          },
          {
            "prestadorId": 6,
            "prestadorNombre": "Laura Benitez",
            "mensaje": "Invitación a cotizar 1001",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.301615Z",
            "habilidadId": 4,
            "rubroId": 3,
            "cotizacionId": null,
            "solicitudId": 1001
          }
        ]
      },
      {
        "solicitudId": 1002,
        "descripcion": "Salta la térmica con frecuencia",
        "estado": "COTIZANDO",
        "fueCotizada": true,
        "esCritica": true,
        "top3": [
          {
            "prestadorId": 4,
            "prestadorNombre": "Sofia Martinez",
            "mensaje": "Invitación a cotizar 1002",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.309851Z",
            "habilidadId": 5,
            "rubroId": 2,
            "cotizacionId": null,
            "solicitudId": 1002
          },
          {
            "prestadorId": 5,
            "prestadorNombre": "Diego Ruiz",
            "mensaje": "Invitación a cotizar 1002",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.312825Z",
            "habilidadId": 5,
            "rubroId": 2,
            "cotizacionId": null,
            "solicitudId": 1002
          },
          {
            "prestadorId": 3,
            "prestadorNombre": "Carlos Lopez",
            "mensaje": "Invitación a cotizar 1002",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.315158Z",
            "habilidadId": 5,
            "rubroId": 2,
            "cotizacionId": null,
            "solicitudId": 1002
          }
        ]
      },
      {
        "solicitudId": 120045,
        "descripcion": "Pérdida en la canilla del baño.",
        "estado": "COTIZANDO",
        "fueCotizada": true,
        "esCritica": false,
        "top3": [
          {
            "prestadorId": 1,
            "prestadorNombre": "Juan Perez",
            "mensaje": "Invitación a cotizar 120045",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.322536Z",
            "habilidadId": 120,
            "rubroId": 1,
            "cotizacionId": null,
            "solicitudId": 120045
          },
          {
            "prestadorId": 7,
            "prestadorNombre": "Marcelo Ibarra",
            "mensaje": "Invitación a cotizar 120045",
            "enviado": true,
            "timestamp": "2025-10-24T18:57:43.325289Z",
            "habilidadId": 120,
            "rubroId": 1,
            "cotizacionId": null,
            "solicitudId": 120045
          }
        ]
      }
    ]
  }
}


"""