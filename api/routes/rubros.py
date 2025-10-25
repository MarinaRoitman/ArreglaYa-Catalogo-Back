from fastapi import APIRouter, Depends, HTTPException
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.rubro import RubroCreate, RubroUpdate, RubroOut
from core.security import require_admin_role
from core.events import publish_event
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/rubros", tags=["Rubros"])

# 🔧 Helper para convertir datos a JSON-safe
def convert_to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_safe(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


@router.post("/", response_model=RubroOut, summary="Crear rubro")
def create_rubro(rubro: RubroCreate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("INSERT INTO rubro (nombre) VALUES (%s)", (rubro.nombre,))
            conn.commit()
            new_id = cursor.lastrowid
            rubro_creado = {"id": new_id, "nombre": rubro.nombre}

            # --- Publicar evento ---
            topic = "rubro"
            event_name = "alta"
            rubro_json = convert_to_json_safe(rubro_creado)
            payload = json.dumps(rubro_json, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                (topic, event_name, payload)
            )
            conn.commit()

            event_id = cursor.lastrowid
            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()

            # Manejar si el cursor devuelve tupla o dict
            if isinstance(event_row, dict):
                created_at_value = event_row.get("created_at")
            else:
                created_at_value = event_row[0] if event_row else None

            # Convertir a datetime ISO-8601 UTC
            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=rubro_json
            )

            return rubro_creado
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[RubroOut], summary="Listar rubros")
def list_rubros(nombre: str = None):
    try:
        with get_connection() as (cursor, conn):
            query = "SELECT id, nombre FROM rubro WHERE 1=1"
            params = []
            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{rubro_id}", response_model=RubroOut, summary="Obtener rubro por ID")
def get_rubro(rubro_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, nombre FROM rubro WHERE id = %s", (rubro_id,))
            rubro = cursor.fetchone()
            if not rubro:
                raise HTTPException(status_code=404, detail="Rubro no encontrado")
            return rubro
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{rubro_id}", response_model=RubroOut, summary="Actualizar rubro")
def update_rubro(rubro_id: int, rubro: RubroUpdate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            fields, values = [], []
            if rubro.nombre is not None:
                fields.append("nombre = %s")
                values.append(rubro.nombre)
            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
            values.append(rubro_id)

            query = f"UPDATE rubro SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rubro no encontrado")

            cursor.execute("SELECT id, nombre FROM rubro WHERE id = %s", (rubro_id,))
            rubro_actualizado = cursor.fetchone()

            # --- Publicar evento ---
            topic = "rubro"
            event_name = "modificacion"
            rubro_json = convert_to_json_safe(rubro_actualizado)
            payload = json.dumps(rubro_json, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                (topic, event_name, payload)
            )
            conn.commit()

            event_id = cursor.lastrowid
            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()

            # Manejar si el cursor devuelve tupla o dict
            if isinstance(event_row, dict):
                created_at_value = event_row.get("created_at")
            else:
                created_at_value = event_row[0] if event_row else None

            # Convertir a datetime ISO-8601 UTC
            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=rubro_json
            )

            return rubro_actualizado
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{rubro_id}", summary="Eliminar rubro")
def delete_rubro(rubro_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, nombre FROM rubro WHERE id = %s", (rubro_id,))
            rubro = cursor.fetchone()
            if not rubro:
                raise HTTPException(status_code=404, detail="Rubro no encontrado")

            cursor.execute("DELETE FROM rubro WHERE id = %s", (rubro_id,))
            conn.commit()

            # --- Publicar evento ---
            topic = "rubro"
            event_name = "baja"
            rubro_json = convert_to_json_safe(rubro)
            payload = json.dumps(rubro_json, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                (topic, event_name, payload)
            )
            conn.commit()

            event_id = cursor.lastrowid
            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()

            # Manejar si el cursor devuelve tupla o dict
            if isinstance(event_row, dict):
                created_at_value = event_row.get("created_at")
            else:
                created_at_value = event_row[0] if event_row else None

            # Convertir a datetime ISO-8601 UTC
            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=rubro_json
            )

            return {"detail": "Rubro eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
