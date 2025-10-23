
import logging, requests

def handle(event_name, payload, api_base_url):
    data = payload.get("cuerpo", {})
    id = data.get("solicitud_id")

    if event_name == "cotizacion.emitida": # representa la creación de un pedido?
        logging.info("📦 Nueva cotización emitida")
        requests.post(f"{api_base_url}/pedidos/", json=data)
    elif event_name == "solicitud.cancelada":
        logging.info("❌ Solicitud cancelada")
        requests.delete(f"{api_base_url}/pedidos/{id}", json=data)
    elif event_name == "cotizacion.aceptada":
        logging.info("✅ Cotización aceptada")
        estado = "aprobado_por_usuario"
        requests.patch(f"{api_base_url}/pedidos/{id}", json=data)
    elif event_name == "cotizacion.rechazada":
        logging.info("🚫 Cotización rechazada")
        requests.delete(f"{api_base_url}/pedidos/{id}", json=data)
    else:
        logging.info(f"Evento de pedido no manejado: {event_name}")


"""
ejemplo cotizacion.emitida:
{
  "squad": "matching",
  "canal": "matching.cotizacion.emitida",
  "evento": "emitida",
  "cuerpo": {
    "cotizacion_id": 111,
    "solicitud_id": 222,
    "usuario_id": 333,
    "prestador_id": 444,
    "monto": 0.00,
  }
}

ejemplo solicitud.cancelada:

{
  "squad": "Búsqueda y Solicitudes",
  "topico": "solicitud",
  "evento": "solicitud.cancelada",
  "cuerpo": {
    "solicitud_id": 120045,
    "usuario_id": 901,
    "motivo": "cambio_de_plan",
    "detalle_motivo": "Lo resolveré por mi cuenta."
  }
}

ejemplo cotizacion.aceptada:
{
  "squad": "Búsqueda y Solicitudes",
  "topico": "cotizacion",
  "evento": "cotizacion.aceptada",
  "cuerpo": {
    "cotizacion_id": 774001,
    "solicitud_id": 120045,
    "usuario_id": 901,
    "prestador_id": 5552,
    "monto": 72000,
    "condiciones": "Incluye materiales menores. No incluye grifería."
  }
}
ejemplo cotizacion.rechazada:
{
  "squad": "Búsqueda y Solicitudes",
  "topico": "cotizacion",
  "evento": "cotizacion.rechazada",
  "cuerpo": {
    "cotizacion_id": 774002,
    "solicitud_id": 120045,
    "usuario_id": 901,
    "prestador_id": 5553,
    "motivo": "precio_alto",
    "comentario": "Me queda alto el presupuesto."
  }
}
"""