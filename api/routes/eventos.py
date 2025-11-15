from fastapi import APIRouter, HTTPException, Depends
from typing import List
from mysql.connector import Error
from core.database import get_connection
from core.security import require_internal_or_admin
from core.events import reprocess_events
from datetime import datetime
import json

router = APIRouter(prefix="/eventos", tags=["Eventos"])

@router.get("/", response_model=List[dict], summary="Listar eventos publicados")
def list_unpublished_events(current_user: dict = Depends(require_internal_or_admin)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, topic, event_name, payload, failed_at FROM unpublished_events ORDER BY failed_at DESC")
            rows = cursor.fetchall()
            events = []
            for row in rows:
                event = {
                    "id": row["id"],
                    "topic": row["topic"],
                    "event_name": row["event_name"],
                    "payload": json.loads(row["payload"]),
                    "failed_at": row["failed_at"].isoformat() if isinstance(row["failed_at"], datetime) else row["failed_at"]
                }
                events.append(event)
            return events
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", summary="Reprocesar eventos no procesados")
def reprocess_unpublished_events(current_user: dict = Depends(require_internal_or_admin)):
    try:
        reprocess_events()
        return {"message": "Reprocesamiento de eventos no procesados iniciado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))