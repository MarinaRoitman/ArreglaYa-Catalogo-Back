import logging, requests


def handle(event_name, payload):
    data = payload.get("payload", {}).get("pedido")
    logging.info(f"Procesando evento de pedido: {event_name} con datos {data}")
    if event_name == "CreatePedido":
        logging.info("👤 Alta de pedido recibida")
        requests.post("http://catalogo:8000/api/pedidos", json=payload) #modificar para que apunte a la url correcta (local o prod)
    elif event_name == "UpdatePedido":
        logging.info("✏️ Actualización de pedido")
        requests.patch("http://catalogo:8000/api/pedidos", json=payload)
    elif event_name == "DeletePedido":
        logging.info("🗑️ Baja de pedido")
        requests.delete("http://catalogo:8000/api/pedidos", json=payload)
    else:
        logging.info(f"Evento de pedido no manejado: {event_name}")
