import json, logging
from core_ack import send_ack
from handlers import users, orders, reviews
from config import get_api_base_url
import os

API_BASE_URL = get_api_base_url()
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN")
        
headers = {
    "x-internal-token": INTERNAL_API_TOKEN,
    "Content-Type": "application/json"
}

def process_message(conn, msg_id):
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM inbound_events WHERE message_id=%s", (msg_id,))
            event = c.fetchone()

        if not event:
            return

        payload = json.loads(event["payload"])
        topic = event["topic"]
        event_name = event["event_name"]
        sub_id = event["subscription_id"]

        logging.info(f"🔍 Procesando {topic} - {event_name}")

        # Despachador según canal (hay que completar con el resto de los canales)
        if topic == "user":
            # Usuarios (clientes, prestadores, admins)
            logging.info("headers inside process_message: ", headers)
            users.handle(event_name, payload, API_BASE_URL, headers)

        # elif topic == "matching" or topic.startswith("solicitud.") or topic.startswith("cotizacion."):
        #     # Se emitió una solicitud con cotizaciones posibles
        #     orders.handle(event_name, payload, API_BASE_URL)

        elif topic == "calificacion":
            # El cliente creó una calificación
            reviews.handle(event_name, payload, API_BASE_URL, headers)

        else:
            logging.info(f"⚠️ Evento no reconocido: {topic}")
            return

        with conn.cursor() as c:
            c.execute("UPDATE inbound_events SET status='done', processed_at=NOW() WHERE message_id=%s", (msg_id,))
        conn.commit()

        #send_ack(msg_id, sub_id)
        logging.info(f"✅ Mensaje procesado OK: {msg_id}")

    except Exception as e:
        logging.exception(f"💥 Error procesando {msg_id}: {e}")
        with conn.cursor() as c:
            c.execute("UPDATE inbound_events SET status='error', error_text=%s WHERE message_id=%s", (str(e), msg_id))
        conn.commit()
