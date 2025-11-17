from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
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
                message_id=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=rubro_json
            )

            return rubro_creado
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[RubroOut], summary="Listar rubros")
def list_rubros(nombre: str = None, activo: bool = None):
    try:
        with get_connection() as (cursor, conn):
            query = "SELECT id, nombre, activo FROM rubro WHERE 1=1 AND activo <> 0"
            params = []
            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            if activo is not None:
                query += " AND activo = %s"
                params.append(activo)
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{rubro_id}", response_model=RubroOut, summary="Obtener rubro por ID")
def get_rubro(rubro_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, nombre, activo FROM rubro WHERE id = %s AND activo <> 0", (rubro_id,))
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
                message_id=str(event_id),
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

            # Obtener todas las habilidades asociadas al rubro
            cursor.execute("SELECT id FROM habilidad WHERE id_rubro = %s", (rubro_id,))
            habilidades = cursor.fetchall()
            habilidad_ids = [row["id"] if isinstance(row, dict) else row[0] for row in habilidades]

            # Para cada habilidad, buscar prestadores afectados, borrar relaciones y publicar eventos
            for habilidad_id in habilidad_ids:
                # Obtener prestadores que tienen esta habilidad
                cursor.execute(
                    "SELECT id_prestador FROM prestador_habilidad WHERE id_habilidad = %s",
                    (habilidad_id,)
                )
                prestadores_afectados = cursor.fetchall()
                prestador_ids = [row["id_prestador"] if isinstance(row, dict) else row[0] for row in prestadores_afectados]

                # Borrar relaciones
                cursor.execute(
                    "DELETE FROM prestador_habilidad WHERE id_habilidad = %s",
                    (habilidad_id,)
                )
                conn.commit()

                # Publicar eventos de modificacion para cada prestador afectado
                for prestador_id in prestador_ids:
                    cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
                    prestador_result = cursor.fetchone()
                    if prestador_result:
                        # Obtener zonas del prestador
                        cursor.execute("""
                            SELECT z.id, z.nombre
                            FROM zona z
                            INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                            WHERE pz.id_prestador = %s
                        """, (prestador_id,))
                        prestador_result["zonas"] = cursor.fetchall()

                        # Obtener habilidades restantes (sin la que se borra)
                        cursor.execute("""
                            SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                            FROM habilidad h
                            INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                            INNER JOIN rubro r ON h.id_rubro = r.id
                            WHERE ph.id_prestador = %s AND h.id != %s
                        """, (prestador_id, habilidad_id))
                        prestador_result["habilidades"] = cursor.fetchall()

                        # Publicar evento de modificacion del prestador
                        topic = "prestador"
                        event_name = "modificacion"
                        prestador_json = convert_to_json_safe(prestador_result)
                        payload_str = json.dumps(prestador_json, ensure_ascii=False)

                        cursor.execute(
                            "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                            (topic, event_name, payload_str)
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
                            message_id=str(event_id),
                            timestamp=timestamp,
                            topic=topic,
                            event_name=event_name,
                            payload=prestador_json
                        )

                # Desactivar la habilidad
                cursor.execute("UPDATE habilidad SET activo = 0 WHERE id = %s", (habilidad_id,))
                conn.commit()

                # Obtener la habilidad para publicar su evento de baja
                cursor.execute("SELECT id, nombre, descripcion, id_rubro, activo FROM habilidad WHERE id = %s", (habilidad_id,))
                habilidad_result = cursor.fetchone()

                # Publicar evento de baja de habilidad
                topic = "habilidad"
                event_name = "baja"
                habilidad_json = convert_to_json_safe(habilidad_result if habilidad_result else {"id": habilidad_id})
                payload_str = json.dumps(habilidad_json, ensure_ascii=False)

                cursor.execute(
                    "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                    (topic, event_name, payload_str)
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
                    message_id=str(event_id),
                    timestamp=timestamp,
                    topic=topic,
                    event_name=event_name,
                    payload=habilidad_json
                )

            # Desactivar el rubro
            cursor.execute("UPDATE rubro SET activo = 0 WHERE id = %s", (rubro_id,))
            conn.commit()

            # Publicar evento de baja del rubro
            topic = "rubro"
            event_name = "baja"
            rubro_actualizado = {"id": rubro["id"], "nombre": rubro["nombre"], "activo": 0}
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
                message_id=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=rubro_json
            )

            return {"detail": "Rubro eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
