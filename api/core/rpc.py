# api/core/rpc.py
import os, json, uuid, pika, threading

RABBIT_HOST = os.getenv("RABBIT_HOST","rabbitmq")
RABBIT_PORT = int(os.getenv("RABBIT_PORT","5672"))
RABBIT_VHOST = os.getenv("RABBIT_VHOST","prestadores")
RABBIT_USER = os.getenv("RABBIT_USER","app")
RABBIT_PASS = os.getenv("RABBIT_PASS","changeme")

_creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
_params = pika.ConnectionParameters(host=RABBIT_HOST, port=RABBIT_PORT,
    virtual_host=RABBIT_VHOST, credentials=_creds, heartbeat=30)

def rpc_login(email: str, password: str, timeout_sec: float = 3.0) -> dict:
    """
    Envía una RPC a usuarios y espera el JWT.
    Devuelve dict con {"ok": True, "token": "..."} o {"ok": False, "error": "..."}.
    """
    corr_id = str(uuid.uuid4())
    conn = pika.BlockingConnection(_params)
    ch = conn.channel()

    # Habilitar direct-reply-to: consumimos de la pseudo-cola especial
    response_holder = {"body": None}
    ev = threading.Event()

    def on_reply(ch, method, props, body):
        if props.correlation_id == corr_id:
            response_holder["body"] = json.loads(body.decode())
            ev.set()

    ch.basic_consume(queue='amq.rabbitmq.reply-to', on_message_callback=on_reply, auto_ack=True)

    # Publicar request
    payload = {"email": email, "password": password}
    ch.basic_publish(
        exchange="rpc",
        routing_key="users.login",
        body=json.dumps(payload),
        properties=pika.BasicProperties(
            reply_to='amq.rabbitmq.reply-to',
            correlation_id=corr_id,
            content_type='application/json'
        )
    )

    # Esperar respuesta (con timeout)
    ch.connection.process_data_events(time_limit=0)  # arranca consumo
    if not ev.wait(timeout_sec):
        try: conn.close()
        except: pass
        return {"ok": False, "error": "timeout waiting users.login"}

    try: conn.close()
    except: pass
    return response_holder["body"]
