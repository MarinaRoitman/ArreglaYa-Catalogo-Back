import json, logging
from core_ack import send_ack
from handlers import users
from config import get_api_base_url


API_BASE_URL = get_api_base_url()


def process_message(conn, msg_id):
    try:
        with conn.cursor() as c:
            c.execute("SELECT * FROM inbound_events WHERE message_id=%s", (msg_id,))
            event = c.fetchone()

        if not event:
            return

        payload = json.loads(event["payload"])
        channel = event["channel"]
        event_name = event["event_name"]
        sub_id = event["subscription_id"]

        logging.info(f"🔍 Procesando {channel} - {event_name}")

        # Despachador según canal (hay que completar con el resto de los canales)
        if channel.startswith("users."):
            users.handle(event_name, payload, API_BASE_URL)
        elif channel.startswith("search.pedido"):
            #pedidos.handle(event_name, payload)
            pass
        else:
            logging.info(f"Evento no reconocido: {channel}")
            return

        with conn.cursor() as c:
            c.execute("UPDATE inbound_events SET status='done', processed_at=NOW() WHERE message_id=%s", (msg_id,))
        conn.commit()

        send_ack(msg_id, sub_id)
        logging.info(f"✅ Mensaje procesado OK: {msg_id}")

    except Exception as e:
        logging.exception(f"💥 Error procesando {msg_id}: {e}")
        with conn.cursor() as c:
            c.execute("UPDATE inbound_events SET status='error', error_text=%s WHERE message_id=%s", (str(e), msg_id))
        conn.commit()
