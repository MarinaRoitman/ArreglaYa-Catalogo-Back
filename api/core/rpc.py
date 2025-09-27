# api/core/rpc.py
import os, json, uuid, time, pika, threading

# ========= Config AMQP (con AMQP_URL opcional) =========
# Orden de resolución:
# 1) AMQP_URL (si está, manda)
# 2) RABBIT_* (host/port/vhost/user/pass)
# Defaults pensados para TÚNEL local en 127.0.0.1:5673

AMQP_URL = os.getenv("AMQP_URL", "").strip()

RABBIT_HOST  = os.getenv("RABBIT_HOST",  "127.0.0.1")   # túnel local por defecto
RABBIT_PORT  = int(os.getenv("RABBIT_PORT", "5673"))    # ssh -L 5673:127.0.0.1:5672
RABBIT_VHOST = os.getenv("RABBIT_VHOST", "prestadores")
RABBIT_USER  = os.getenv("RABBIT_USER",  "admin")
RABBIT_PASS  = os.getenv("RABBIT_PASS",  "LETMEINTHERABBIT!!!1")

def _build_params():
    if AMQP_URL:
        print(f"[rpc] Using AMQP_URL={AMQP_URL}")
        return pika.URLParameters(AMQP_URL)
    print(f"[rpc] Using host={RABBIT_HOST} port={RABBIT_PORT} vhost={RABBIT_VHOST} user={RABBIT_USER}")
    creds  = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    return pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        virtual_host=RABBIT_VHOST,
        credentials=creds,
        heartbeat=30,
        blocked_connection_timeout=5,
        connection_attempts=3,
        retry_delay=2,
        client_properties={"connection_name": "api-rpc-client"}
    )

_params = _build_params()

# ========= RPC login =========
def rpc_login(email: str, password: str, timeout_sec: float = 4.0) -> dict:
    """
    RPC a users.login con direct-reply-to.
    Devuelve {"ok": True, "token": "..."} o {"ok": False, "error": "..."}.
    """
    corr_id = str(uuid.uuid4())
    conn = None
    try:
        conn = pika.BlockingConnection(_params)
        ch = conn.channel()

        # Asegurar exchange 'rpc' como DIRECT sin cambiar su tipo si ya existe.
        try:
            ch.exchange_declare(exchange="rpc", exchange_type="direct", durable=True, passive=True)
        except pika.exceptions.ChannelClosedByBroker as e:
            # 404 (no existe): crearlo como direct.
            if getattr(e, "reply_code", None) == 404:
                ch = conn.channel()
                ch.exchange_declare(exchange="rpc", exchange_type="direct", durable=True)
            else:
                raise

        # Consumidor de respuesta (direct-reply-to)
        ev = threading.Event()
        holder = {"resp": None}

        def on_reply(_ch, _method, props, body):
            if props.correlation_id == corr_id:
                try:
                    holder["resp"] = json.loads(body.decode())
                except Exception:
                    holder["resp"] = {"ok": False, "error": "bad_json"}
                ev.set()

        ch.basic_consume(queue="amq.rabbitmq.reply-to", on_message_callback=on_reply, auto_ack=True)

        # Publicar request
        payload = {"email": email, "password": password}
        print(f"[rpc] publish users.login → exchange=rpc key=users.login corr_id={corr_id}")
        ch.basic_publish(
            exchange="rpc",
            routing_key="users.login",
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                reply_to="amq.rabbitmq.reply-to",
                correlation_id=corr_id,
                content_type="application/json"
            )
        )

        # Espera activa bombeando frames para que llegue la respuesta
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            conn.process_data_events(time_limit=0.2)
            if ev.is_set():
                break

        if not ev.is_set():
            return {"ok": False, "error": "timeout waiting users.login"}

        return holder["resp"] or {"ok": False, "error": "empty_response"}

    except pika.exceptions.AMQPError as e:
        return {"ok": False, "error": f"amqp_error: {type(e).__name__}"}
    except Exception as e:
        return {"ok": False, "error": f"unexpected_error: {type(e).__name__}: {e}"}
    finally:
        try:
            if conn and conn.is_open:
                conn.close()
        except Exception:
            pass
