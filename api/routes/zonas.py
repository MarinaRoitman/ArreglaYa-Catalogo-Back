from fastapi import APIRouter, HTTPException, Depends
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.zona import ZonaCreate, ZonaUpdate, ZonaOut
from core.security import require_admin_role
from core.events import publish_event
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/zonas", tags=["Zonas"])

@router.post("/", response_model=ZonaOut, summary="Crear zona")
def create_zona(zona: ZonaCreate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("INSERT INTO zona (nombre) VALUES (%s)", (zona.nombre,))
            conn.commit()
            new_id = cursor.lastrowid
            zona_creada = {"id": new_id, "nombre": zona.nombre}

            # Registrar evento en la tabla
            topic = "zona"
            event_name = "alta"
            payload = json.dumps(zona_creada, ensure_ascii=False)

            insert_event_query = """
                INSERT INTO eventos_publicados (topic, event_name, payload)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_event_query, (topic, event_name, payload))
            conn.commit()

            event_id = cursor.lastrowid
            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else event_row[0]

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            # Publicar evento en CoreHub
            publish_event(
                message_id=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=zona_creada
            )

            return zona_creada
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ZonaOut], summary="Listar zonas")
def list_zonas(nombre: str = None):
    try:
        with get_connection() as (cursor, conn):
            
            query = "SELECT id, nombre FROM zona WHERE 1=1"
            params = []
            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{zona_id}", response_model=ZonaOut, summary="Obtener zona por ID")
def get_zona(zona_id: int):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("SELECT id, nombre FROM zona WHERE id = %s", (zona_id,))
            zona = cursor.fetchone()
            if not zona:
                raise HTTPException(status_code=404, detail="Zona no encontrada")
            return zona
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{zona_id}", response_model=ZonaOut, summary="Modificar zona")
def update_zona(zona_id: int, zona: ZonaUpdate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            fields = []
            values = []
            for key, value in zona.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)
            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")
            values.append(zona_id)
            query = f"UPDATE zona SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Zona no encontrada")

            cursor.execute("SELECT id, nombre FROM zona WHERE id=%s", (zona_id,))
            zona_modificada = cursor.fetchone()

            # Registrar evento en la tabla
            topic = "zona"
            event_name = "modificacion"
            payload = json.dumps(zona_modificada, ensure_ascii=False)

            insert_event_query = """
                INSERT INTO eventos_publicados (topic, event_name, payload)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_event_query, (topic, event_name, payload))
            conn.commit()

            event_id = cursor.lastrowid
            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else event_row[0]

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            # Publicar evento en CoreHub
            publish_event(
                message_id=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=zona_modificada
            )

            return zona_modificada
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{zona_id}", summary="Eliminar zona")
def delete_zona(zona_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, nombre FROM zona WHERE id = %s", (zona_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Zona no encontrada")
            nombre = row["nombre"] if isinstance(row, dict) else row[1]
            
            cursor.execute("DELETE FROM zona WHERE id=%s", (zona_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Zona no encontrada")

            # Registrar evento en la tabla
            topic = "zona"
            event_name = "baja"
            payload = json.dumps({"id": zona_id, "nombre": nombre}, ensure_ascii=False)

            insert_event_query = """
                INSERT INTO eventos_publicados (topic, event_name, payload)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_event_query, (topic, event_name, payload))
            conn.commit()

            event_id = cursor.lastrowid
            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else event_row[0]

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            # Publicar evento en CoreHub
            publish_event(
                message_id=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload={"id": zona_id, "nombre": nombre}
            )

            return {"detail": f"Zona {zona_id} eliminada correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))