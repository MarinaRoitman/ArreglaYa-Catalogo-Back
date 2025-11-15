
import json
import os
import requests
from datetime import datetime, timezone
from core.database import get_connection
from dotenv import load_dotenv

load_dotenv()

CORE_URL = "https://api.arreglacore.click/publish"
CORE_API_KEY = os.getenv("CORE_API_KEY")

def publish_event(message_id: str, timestamp: str, topic: str, event_name: str, payload: dict):
    """
    Publica un evento al Core Hub con el nuevo formato (topic + eventName).
    """
    headers = {
        "X-API-KEY": CORE_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "messageId": message_id,
        "timestamp": timestamp,
        "destination": {
            "topic": topic,
            "eventName": event_name
        },
        "payload": payload
    }

    print(f"➡️ URL: {CORE_URL}")
    print(f"➡️ Headers: {headers}")
    print(f"➡️ Body JSON:\n{json.dumps(body, indent=4, ensure_ascii=False)}")
        
    response = requests.post(CORE_URL, headers=headers, json=body)
    
    print(f"Respuesta del corehub====")
    print(f"⬅️ Código HTTP: {response.status_code}")
    print(f"⬅️ Texto completo:\n{response.text}")
    
    if response.status_code < 200 or response.status_code >= 300:
        print("❌ Error al publicar el evento, se agregará a eventos no procesados.")
        add_unprocessed_event(message_id, topic, event_name, payload)

    return response

def add_unprocessed_event(message_id: str, topic: str, event_name: str, payload: dict):
    """
    Agrega un evento no procesado a la tabla de eventos no procesados.
    """
    try:
        with get_connection() as (cursor, conn):
            payload_str = json.dumps(payload, ensure_ascii=False)
            print("Insertando evento no procesado en la base de datos...")
            cursor.execute(
                "INSERT INTO unpublished_events (message_id, topic, event_name, payload) VALUES (%s, %s, %s, %s)",
                (message_id, topic, event_name, payload_str)
            )
            conn.commit()
            print("✅ Evento no procesado agregado (en teoría...).")
    except Exception as e:
        print(f"Error al agregar evento no procesado {message_id}: {e}")

def reprocess_events():
    """
    Reprocesa los eventos no procesados intentando publicarlos nuevamente.
    """
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, message_id, topic, event_name, payload FROM unpublished_events")
            events = cursor.fetchall()
            print(f"Se encontraron {len(events)} eventos no procesados para reprocesar.")

            for event in events:
                event_id = event["id"]
                message_id = event["message_id"]
                topic = event["topic"]
                event_name = event["event_name"]
                payload_str = event["payload"]

                try:
                    payload = json.loads(payload_str)
                except json.JSONDecodeError:
                    print(f"❌ Error al decodificar el payload del evento {message_id}, se eliminará.")
                    cursor.execute("DELETE FROM unpublished_events WHERE id = %s", (event_id,))
                    conn.commit()
                    continue

                timestamp = datetime.now(timezone.utc).isoformat()

                print(f"Reprocesando evento {message_id}...")
                publish_event(message_id, timestamp, topic, event_name, payload)

                # Si la publicación fue exitosa, eliminar el evento de la tabla
                print(f"Eliminando evento {message_id} de la tabla de no procesados...")
                cursor.execute("DELETE FROM unpublished_events WHERE id = %s", (event_id,))
                conn.commit()
                print(f"✅ Evento {message_id} reprocesado y eliminado.")
    except Exception as e:
        print(f"Error al reprocesar eventos no procesados: {e}")