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
        # --------------------
        # 1) Obtener evento
        # --------------------
        with conn.cursor() as c:
            c.execute("SELECT * FROM inbound_events WHERE message_id=%s", (msg_id,))
            event = c.fetchone()

        if not event:
            logging.warning(f" Mensaje no encontrado en inbound_events: {msg_id}")
            return

        topic = event.get("topic")
        event_name = event.get("event_name")
        sub_id = event.get("subscription_id")

        # --------------------
        # 2) Validaciones básicas
        # --------------------
        if not topic or not event_name:
            logging.error(f"❌ Evento inválido en DB (topic/event_name faltan) → msg_id={msg_id}")
            return

        try:
            payload = json.loads(event["payload"])
        except Exception:
            logging.error(f"❌ Payload inválido (no es JSON válido) → msg_id={msg_id}")
            return

        logging.info(f"🔍 Procesando evento → topic={topic} | event={event_name}")

        # --------------------
        # 3) Dispatch según topic
        # --------------------
        if topic == "user":
            users.handle(event_name, payload, API_BASE_URL, headers)

        elif topic == "calificacion":
            reviews.handle(event_name, payload, API_BASE_URL, headers)

        elif topic in ("solicitud", "cotizacion"):
            # La cancelación en matching implica rechazo en ORDERS
            orders.handle(event_name, payload, API_BASE_URL, headers)

        else:
            logging.info(f"⚠️ Topic no reconocido, evento ignorado → topic={topic}")
            return

        # --------------------
        # 4) Marcar como procesado
        # --------------------
        with conn.cursor() as c:
            c.execute("""
                UPDATE inbound_events 
                SET status='done', processed_at=NOW() 
                WHERE message_id=%s
            """, (msg_id,))
        conn.commit()

        # --------------------
        # 5) ACK al Core
        # --------------------
        send_ack(msg_id, sub_id)

        logging.info(f"✅ Mensaje procesado correctamente → msg_id={msg_id}")

    except Exception as e:
        # --------------------
        # 6) Error en procesamiento
        # --------------------
        logging.exception(f"💥 Error procesando msg_id={msg_id}: {e}")

        with conn.cursor() as c:
            c.execute("""
                UPDATE inbound_events 
                SET status='error', error_text=%s 
                WHERE message_id=%s
            """, (str(e), msg_id))
        conn.commit()

