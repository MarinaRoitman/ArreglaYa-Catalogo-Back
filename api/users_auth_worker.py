# users_auth_worker.py
import socket, sys, json, pika, jwt
from datetime import datetime, timedelta

# --- Fixed config (matches your SSH tunnel and broker) ---
RABBIT_HOST  = "127.0.0.1"     # local end of your ssh -L
RABBIT_PORT  = 5673            # you forwarded 5673 -> remote 5672
RABBIT_VHOST = "prestadores"
RABBIT_USER  = "admin"
RABBIT_PASS  = "LETMEINTHERABBIT!!!1"

JWT_SECRET   = "mi_clave_secreta_super_segura"
JWT_ALGO     = "HS256"

# --- Sanity: can we reach local tunnel? ---
print(f"[sanity] Probandoconexión a {RABBIT_HOST}:{RABBIT_PORT} ...")
try:
    sock = socket.create_connection((RABBIT_HOST, RABBIT_PORT), timeout=5)
    sock.close()
    print(f"[sanity] ✔ RabbitMQ responde en el puerto {RABBIT_PORT}")
except Exception as e:
    print(f"[sanity] ✘ No pude conectar a {RABBIT_HOST}:{RABBIT_PORT}: {e}")
    sys.exit(1)

# --- Pika connection params ---
creds  = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
params = pika.ConnectionParameters(
    host=RABBIT_HOST,
    port=RABBIT_PORT,
    virtual_host=RABBIT_VHOST,
    credentials=creds,
    heartbeat=30,
    blocked_connection_timeout=10,
    connection_attempts=3,
    retry_delay=2
)

def create_jwt(user_id, email):
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def validate_user(email, password):
    # TODO: reemplazar por consulta real a tu DB
    if email == "ori@example.com" and password == "supersecret":
        return {"id": 1, "email": email}
    return None

def on_request(ch, method, props, body):
    try:
        data = json.loads(body.decode())
        email = data.get("email")
        password = data.get("password")
        print(f"[worker] Recibí login: email='{email}', reply_to='{props.reply_to}'")

        user = validate_user(email, password)
        if user:
            token = create_jwt(user["id"], user["email"])
            resp = {"ok": True, "token": token}
        else:
            resp = {"ok": False, "error": "invalid_credentials"}
    except Exception as e:
        resp = {"ok": False, "error": "server_error", "msg": str(e)}

    ch.basic_publish(
        exchange="",
        routing_key=props.reply_to,
        properties=pika.BasicProperties(
            correlation_id=props.correlation_id,
            content_type="application/json"
        ),
        body=json.dumps(resp)
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)

def ensure_direct_exchange(ch, name):
    """Use existing 'name' if present; create as direct if missing.
    Avoid type mismatch explosions."""
    try:
        # passive=True: just check it exists; don’t change its type
        ch.exchange_declare(exchange=name, exchange_type="direct", durable=True, passive=True)
        return ch
    except pika.exceptions.ChannelClosedByBroker as e:
        # 404 = not found: reopen channel and create it
        if getattr(e, "reply_code", None) == 404:
            ch = ch.connection.channel()
            ch.exchange_declare(exchange=name, exchange_type="direct", durable=True, passive=False)
            return ch
        # any other error (like type mismatch) -> rethrow
        raise

def main():
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Ensure exchange 'rpc' as DIRECT (matches broker)
    ch = ensure_direct_exchange(ch, "rpc")

    # Service queue bound to 'rpc' with routing key users.login
    qname = "rpc.users.login"
    ch.queue_declare(queue=qname, durable=True)
    ch.queue_bind(queue=qname, exchange="rpc", routing_key="users.login")

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=qname, on_message_callback=on_request)

    print("[worker] Esperando mensajes en rpc.users.login ...")
    ch.start_consuming()

if __name__ == "__main__":
    main()
