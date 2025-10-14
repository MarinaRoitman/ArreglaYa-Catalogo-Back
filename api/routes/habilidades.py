from fastapi import APIRouter, HTTPException, Depends
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.habilidad import HabilidadCreate, HabilidadUpdate, HabilidadOut
from core.security import require_admin_role 
import json
from datetime import datetime, timezone
from core.events import publish_event

router = APIRouter(prefix="/habilidades", tags=["Habilidades"])

# Crear habilidad
@router.post("/", response_model=HabilidadOut, summary="Crear habilidad")
def create_habilidad(habilidad: HabilidadCreate):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute(
                "INSERT INTO habilidad (nombre, descripcion, id_rubro) VALUES (%s, %s, %s)",
                (habilidad.nombre, habilidad.descripcion, habilidad.id_rubro)
            )
            conn.commit()
            # Obtener el id de la habilidad recién creada antes de publicar
            habilidad_id = cursor.lastrowid

            # Preparar payload como dict (serializable)
            habilidad_creada = {
                "id": habilidad_id,
                "nombre": habilidad.nombre,
                "descripcion": habilidad.descripcion,
                "id_rubro": habilidad.id_rubro,
            }

            # Publicar evento de creación (guardar en tabla y enviar)
            channel = "catalogue.habilidad.creacion"
            event_name = "creacion_habilidad"
            payload_str = json.dumps(habilidad_creada, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (channel, event_name, payload) VALUES (%s, %s, %s)",
                (channel, event_name, payload_str)
            )
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else (event_row[0] if event_row else None)

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                channel=channel,
                eventName=event_name,
                payload=habilidad_creada,
            )

            return habilidad_creada
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Listar habilidades
@router.get("/", response_model=List[HabilidadOut], summary="Listar habilidades")
def list_habilidades(nombre: str = None, id_rubro: int = None):
    try:
        with get_connection() as (cursor, conn):
            query = "SELECT id, nombre, descripcion, id_rubro FROM habilidad WHERE 1=1"
            params = []
            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            if id_rubro:
                query += " AND id_rubro = %s"
                params.append(id_rubro)

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{habilidad_id}", response_model=HabilidadOut, summary="Obtener habilidad por ID")
def get_habilidad(habilidad_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, nombre, descripcion, id_rubro FROM habilidad WHERE id = %s", (habilidad_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Habilidad no encontrada")
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar habilidad
@router.put("/{habilidad_id}", response_model=HabilidadOut, summary="Actualizar habilidad")
def update_habilidad(habilidad_id: int, habilidad: HabilidadUpdate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            # Construir SET dinámico
            fields = []
            values = []
            if habilidad.nombre is not None:
                fields.append("nombre = %s")
                values.append(habilidad.nombre)
            if habilidad.descripcion is not None:
                fields.append("descripcion = %s")
                values.append(habilidad.descripcion)
            if habilidad.id_rubro is not None:
                fields.append("id_rubro = %s")
                values.append(habilidad.id_rubro)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

            query = f"UPDATE habilidad SET {', '.join(fields)} WHERE id = %s"
            values.append(habilidad_id)

            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Habilidad no encontrada")

            cursor.execute("SELECT id, nombre, descripcion, id_rubro FROM habilidad WHERE id = %s", (habilidad_id,))
            updated = cursor.fetchone()

            # Publicar evento de modificación (mismo patrón que zonas)
            channel = "catalogue.habilidad.modificacion"
            event_name = "modificacion_habilidad"
            payload = json.dumps(updated, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO eventos_publicados (channel, event_name, payload) VALUES (%s, %s, %s)",
                (channel, event_name, payload)
            )
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else (event_row[0] if event_row else None)

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                channel=channel,
                eventName=event_name,
                payload=updated,
            )

            return updated
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar habilidad
@router.delete("/{habilidad_id}", summary="Eliminar habilidad")
def delete_habilidad(habilidad_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            # Intentar baja lógica: actualizar campo 'activo' a False
            try:
                cursor.execute("UPDATE habilidad SET activo = %s WHERE id = %s", (False, habilidad_id))
                conn.commit()
            except Error as e:
                # Si la columna 'activo' no existe, fallback a borrado físico
                msg = str(e).lower()
                if "unknown column" in msg or "columna" in msg:
                    cursor.execute("DELETE FROM habilidad WHERE id = %s", (habilidad_id,))
                    conn.commit()
                else:
                    raise

            # Verificar existencia / afectación
            if cursor.rowcount == 0:
                # Puede ser que el UPDATE no haya afectado filas; verificar existencia
                cursor.execute("SELECT id FROM habilidad WHERE id = %s", (habilidad_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Habilidad no encontrada")

            # Obtener registro actualizado para publicar
            cursor.execute("SELECT id, nombre, descripcion, id_rubro, activo FROM habilidad WHERE id = %s", (habilidad_id,))
            registro = cursor.fetchone()

            # Publicar evento de baja
            channel = "catalogue.habilidad.baja"
            event_name = "baja_habilidad"
            payload = json.dumps(registro if registro else {"id": habilidad_id}, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO eventos_publicados (channel, event_name, payload) VALUES (%s, %s, %s)",
                (channel, event_name, payload)
            )
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else (event_row[0] if event_row else None)

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                channel=channel,
                eventName=event_name,
                payload=registro if registro else {"id": habilidad_id},
            )

            return {"detail": "Habilidad marcada como inactiva"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


"""@router.post("/{habilidad_id}/reactivar", summary="Reactivar habilidad")
def reactivate_habilidad(habilidad_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            # Intentar activar la habilidad
            cursor.execute("UPDATE habilidad SET activo = %s WHERE id = %s", (True, habilidad_id))
            conn.commit()

            if cursor.rowcount == 0:
                # Verificar existencia
                cursor.execute("SELECT id FROM habilidad WHERE id = %s", (habilidad_id,))
                if not cursor.fetchone():
                    raise HTTPException(status_code=404, detail="Habilidad no encontrada")

            cursor.execute("SELECT id, nombre, descripcion, id_rubro, activo FROM habilidad WHERE id = %s", (habilidad_id,))
            registro = cursor.fetchone()

            # Publicar evento de reactivación
            channel = "catalogue.habilidad.reactivacion"
            event_name = "reactivacion_habilidad"
            payload = json.dumps(registro if registro else {"id": habilidad_id}, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO eventos_publicados (channel, event_name, payload) VALUES (%s, %s, %s)",
                (channel, event_name, payload)
            )
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            created_at_value = event_row["created_at"] if isinstance(event_row, dict) else (event_row[0] if event_row else None)

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                channel=channel,
                eventName=event_name,
                payload=registro if registro else {"id": habilidad_id},
            )

            return {"detail": "Habilidad reactivada"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))"""
