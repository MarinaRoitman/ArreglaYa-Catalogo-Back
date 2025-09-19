# api/core/events.py
import json
import os
import threading
import time
from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
RABBIT_VHOST = os.getenv("RABBIT_VHOST", "prestadores")
RABBIT_USER = os.getenv("RABBIT_USER") or os.getenv("RABBIT_APP_USER", "app")
RABBIT_PASS = os.getenv("RABBIT_PASS") or os.getenv("RABBIT_APP_PASS", "changeme")

_EXCHANGE = "events"
_EXCHANGE_TYPE = "topic"

_connection: Optional[pika.BlockingConnection] = None
_channel: Optional[BlockingChannel] = None
_lock = threading.Lock()


def _connect() -> None:
    """Crea conexión/canal y asegura que exista el exchange."""
    global _connection, _channel
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        virtual_host=RABBIT_VHOST,
        credentials=creds,
        heartbeat=30,
        blocked_connection_timeout=10,
        connection_attempts=5,
        retry_delay=2,
    )
    _connection = pika.BlockingConnection(params)
    _channel = _connection.channel()
    _channel.exchange_declare(exchange=_EXCHANGE, exchange_type=_EXCHANGE_TYPE, durable=True)


def _get_channel() -> BlockingChannel:
    global _channel
    with _lock:
        if _channel is None or _channel.is_closed:
            _connect()
    return _channel  # type: ignore[return-value]


def publish_event(routing_key: str, payload: dict) -> bool:
    """
    Publica un evento persistente en el exchange 'events'.
    Reintenta suave si hay error, pero NUNCA rompe tu request.
    """
    global _connection, _channel
    body = json.dumps(payload).encode("utf-8")

    for attempt in range(3):
        try:
            ch = _get_channel()
            ch.basic_publish(
                exchange=_EXCHANGE,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,  # persistente
                ),
                mandatory=False,
            )
            return True
        except Exception:
            # pequeño backoff y forzar reconexión para el próximo intento
            time.sleep(0.5 * (attempt + 1))
            with _lock:
                try:
                    if _connection and _connection.is_open:
                        _connection.close()
                except Exception:
                    pass
                finally:
                    _connection = None
                    _channel = None
    return False
