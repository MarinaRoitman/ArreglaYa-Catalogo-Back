# routes/prestadores.py
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.prestador import PrestadorCreate, PrestadorUpdate, PrestadorOut
from core.security import get_password_hash, require_admin_role, require_prestador_role, require_admin_or_prestador_role
from decimal import Decimal
import json
from datetime import datetime, timezone
from core.events import publish_event
from services.validaciones import chequear_pedidos_activos_por_habilidad, chequear_pedidos_activos_por_zona
import logging as logger

logger = logger.getLogger(__name__)

router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

def convert_to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_safe(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

# Listar todos con filtros opcionales
@router.get("/", response_model=List[PrestadorOut],
            summary="Listar prestadores",
            description="Obtiene una lista de prestadores filtrando opcionalmente por nombre, apellido, email, teléfono, dirección o zona mediante parámetro.")
def list_prestadores(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    estado: Optional[str] = None,
    ciudad: Optional[str] = None,
    calle: Optional[str] = None,
    numero: Optional[str] = None,
    piso: Optional[str] = None,
    departamento: Optional[str] = None,
    id_zona: Optional[int] = None,
    dni: Optional[str] = None,
    activo: Optional[bool] = None,
    current_user: dict = Depends(require_admin_role)
):
    try:        
        with get_connection() as (cursor, conn):
            query = "SELECT * FROM prestador WHERE 1 = 1"
            params = []

            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            if apellido:
                query += " AND apellido LIKE %s"
                params.append(f"%{apellido}%")
            if email:
                query += " AND email LIKE %s"
                params.append(f"%{email}%")
            if telefono:
                query += " AND telefono LIKE %s"
                params.append(f"%{telefono}%")
            if id_zona:
                query += " AND id_zona = %s"
                params.append(id_zona)
            if dni:
                query += " AND dni LIKE %s"
                params.append(f"%{dni}%")
            if activo is not None:
                query += " AND activo = %s"
                params.append(activo)
            if estado:
                query += " AND estado LIKE %s"
                params.append(f"%{estado}%")
            if ciudad:
                query += " AND ciudad LIKE %s"
                params.append(f"%{ciudad}%")
            if calle:
                query += " AND calle LIKE %s"
                params.append(f"%{calle}%")
            if numero:
                query += " AND numero LIKE %s"
                params.append(f"%{numero}%")
            if piso:
                query += " AND piso LIKE %s"
                params.append(f"%{piso}%")
            if departamento:
                query += " AND departamento LIKE %s"
                params.append(f"%{departamento}%")
                

            cursor.execute(query, tuple(params))
            prestadores = cursor.fetchall()

            # Para cada prestador, obtener sus zonas y habilidades (con nombre de rubro)
            for prestador in prestadores:
                # Zonas
                cursor.execute("""
                    SELECT z.id, z.nombre
                    FROM zona z
                    INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                    WHERE pz.id_prestador = %s
                """, (prestador["id"],))
                prestador["zonas"] = cursor.fetchall()
                # Habilidades con nombre de rubro
                cursor.execute("""
                    SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                    FROM habilidad h
                    INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                    INNER JOIN rubro r ON h.id_rubro = r.id
                    WHERE ph.id_prestador = %s
                """, (prestador["id"],))
                prestador["habilidades"] = cursor.fetchall()
            return prestadores
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener un prestador por ID
@router.get("/{prestador_id}", response_model=PrestadorOut)
def get_prestador(prestador_id: int, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")
            
            # Obtener zonas del prestador
            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            zonas = cursor.fetchall()
            result["zonas"] = zonas
            
            # Obtener habilidades del prestador con nombre de rubro
            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            habilidades = cursor.fetchall()
            result["habilidades"] = habilidades

            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar un prestador
@router.patch("/{prestador_id}", response_model=PrestadorOut)
def update_prestador(prestador_id: int, prestador: PrestadorUpdate, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:        
        with get_connection() as (cursor, conn):

            # Validar que el prestador exista
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")
            
            fields = []
            values = []
            data = prestador.model_dump(exclude_unset=True)

            # Validar email duplicado (si se envía)
            if prestador.email:
                cursor.execute("SELECT id FROM prestador WHERE email = %s AND id != %s", (prestador.email, prestador_id))
                if cursor.fetchone():
                    raise HTTPException(status_code=409, detail="Email ya registrado en otro prestador")
            
            # Validar dni duplicado (si se envía)
            if prestador.dni:
                cursor.execute("SELECT id FROM prestador WHERE dni = %s AND id != %s", (prestador.dni, prestador_id))
                if cursor.fetchone():
                    raise HTTPException(status_code=409, detail="DNI ya registrado en otro prestador")

            # validar que hayan datos que actualizar
            if not data:
                raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")
            # validar que el teléfono sea numérico
            if "telefono" in data and data["telefono"] and not data["telefono"].isdigit():
                raise HTTPException(status_code=400, detail="El teléfono debe ser numérico")
            if "dni" in data and data["dni"] and not data["dni"].isdigit():
                raise HTTPException(status_code=400, detail="El dni debe ser numérico")
            if "contrasena" in data and data.get("contrasena"):
                hashed_password = get_password_hash(data["contrasena"])
                fields.append("password=%s")
                values.append(hashed_password)
                del data["contrasena"]

            for key, value in data.items():
                fields.append(f"{key}=%s")
                values.append(value)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

            values.append(prestador_id)
            query = f"UPDATE prestador SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            cursor.execute("SELECT * FROM prestador WHERE id=%s", (prestador_id,))
            result = cursor.fetchone()
            
            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            result["zonas"] = cursor.fetchall()

            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            result["habilidades"] = cursor.fetchall()

            # --- Publicar evento de modificación ---
            topic = "prestador"
            event_name = "modificacion"
            prestador_json = convert_to_json_safe(result)
            payload_str = json.dumps(prestador_json, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                (topic, event_name, payload_str)
            )
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            if isinstance(event_row, dict):
                created_at_value = event_row.get("created_at")
            else:
                created_at_value = event_row[0] if event_row else None

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=prestador_json
            )

            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar un prestador
@router.delete("/{prestador_id}")
def delete_prestador(prestador_id: int, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            # Baja lógica: actualizar campo activo a False
            cursor.execute("UPDATE prestador SET activo = %s WHERE id=%s", (False, prestador_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            # Obtener el prestador actualizado
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            prestador_actualizado = cursor.fetchone()
            
            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["zonas"] = cursor.fetchall()

            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["habilidades"] = cursor.fetchall()

            # --- Publicar evento de baja ---
            topic = "prestador"
            event_name = "baja"
            prestador_json = convert_to_json_safe(prestador_actualizado)
            payload_str = json.dumps(prestador_json, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
                (topic, event_name, payload_str)
            )
            conn.commit()
            event_id = cursor.lastrowid

            cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
            event_row = cursor.fetchone()
            if isinstance(event_row, dict):
                created_at_value = event_row.get("created_at")
            else:
                created_at_value = event_row[0] if event_row else None

            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()
            else:
                timestamp = datetime.now(timezone.utc).isoformat()

            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=prestador_json
            )

            return {"detail": f"Prestador {prestador_id} dado de baja correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{prestador_id}/zonas", summary="Agregar zona a prestador")
def add_zona_to_prestador(
    prestador_id: int,
    id_zona: int = Body(..., embed=True),
    current_user: dict = Depends(require_admin_or_prestador_role)
):
    try:
        with get_connection() as (cursor, conn):
            # Validar existencia de la zona
            cursor.execute("SELECT id FROM zona WHERE id = %s", (id_zona,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Zona no encontrada")

            # verificar que no exista ya la zona en el prestador
            cursor.execute(
                "SELECT id FROM prestador_zona WHERE id_prestador = %s AND id_zona = %s",
                (prestador_id, id_zona)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="La zona ya está asociada al prestador")


            cursor.execute(
                "INSERT INTO prestador_zona (id_prestador, id_zona) VALUES (%s, %s)",
                (prestador_id, id_zona)
            )
            conn.commit()

            # Obtener prestador actualizado con zonas y habilidades
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            prestador_actualizado = cursor.fetchone()
            if not prestador_actualizado:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["zonas"] = cursor.fetchall()

            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["habilidades"] = cursor.fetchall()

            # Publicar evento de modificación (mismo topic/event_name que el update)
            topic = "prestador"
            event_name = "modificacion"
            prestador_json = convert_to_json_safe(prestador_actualizado)
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
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=prestador_json
            )

            return {"detail": f"Zona {id_zona} agregada al prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

#Eliminar zona del prestador
@router.delete("/{prestador_id}/zonas", summary="Quitar zona a prestador")
def remove_zona_from_prestador(
    prestador_id: int,
    id_zona: int = Body(..., embed=True),
    current_user: dict = Depends(require_admin_or_prestador_role)
):
    try:
        with get_connection() as (cursor, conn):
            # validar solicitudes activas
            chequear_pedidos_activos_por_zona(prestador_id, id_zona, cursor)
            
            cursor.execute(
                "DELETE FROM prestador_zona WHERE id_prestador = %s AND id_zona = %s",
                (prestador_id, id_zona)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Relación no encontrada")

            # Obtener prestador actualizado con zonas y habilidades
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            prestador_actualizado = cursor.fetchone()
            if not prestador_actualizado:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["zonas"] = cursor.fetchall()

            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["habilidades"] = cursor.fetchall()

            # Publicar evento de modificación
            topic = "prestador"
            event_name = "modificacion"
            prestador_json = convert_to_json_safe(prestador_actualizado)
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
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=prestador_json
            )

            return {"detail": f"Zona {id_zona} quitada del prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


#Listar prestadores por zona
@router.get("/zona/{id_zona}", response_model=List[PrestadorOut], summary="Listar prestadores por zona")
def get_prestadores_by_zona(
    id_zona: int,
    current_user: dict = Depends(require_admin_role)
):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("""
                SELECT p.*
                FROM prestador p
                INNER JOIN prestador_zona pz ON p.id = pz.id_prestador
                WHERE pz.id_zona = %s
            """, (id_zona,))
            prestadores = cursor.fetchall()
            # Para cada prestador, obtener sus zonas y habilidades (con nombre de rubro)
            for prestador in prestadores:
                # Zonas
                cursor.execute("""
                    SELECT z.id, z.nombre
                    FROM zona z
                    INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                    WHERE pz.id_prestador = %s
                """, (prestador["id"],))
                prestador["zonas"] = cursor.fetchall()
                # Habilidades con nombre de rubro
                cursor.execute("""
                    SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                    FROM habilidad h
                    INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                    INNER JOIN rubro r ON h.id_rubro = r.id
                    WHERE ph.id_prestador = %s
                """, (prestador["id"],))
                prestador["habilidades"] = cursor.fetchall()
            return prestadores
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

#Agregar habilidad al prestador
@router.post("/{prestador_id}/habilidades", summary="Agregar habilidad a prestador")
def add_habilidad_to_prestador(
    prestador_id: int,
    id_habilidad: int = Body(..., embed=True),
    current_user: dict = Depends(require_admin_or_prestador_role)
):
    try:
        with get_connection() as (cursor, conn):
            # Validar existencia de la habilidad
            cursor.execute("SELECT id FROM habilidad WHERE id = %s", (id_habilidad,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Habilidad no encontrada")

            # verificar que no exista ya la habilidad en el prestador
            cursor.execute(
                "SELECT id FROM prestador_habilidad WHERE id_prestador = %s AND id_habilidad = %s",
                (prestador_id, id_habilidad)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="La habilidad ya está asociada al prestador")
            
            cursor.execute(
                "INSERT INTO prestador_habilidad (id_prestador, id_habilidad) VALUES (%s, %s)",
                (prestador_id, id_habilidad)
            )
            conn.commit()

            # Obtener prestador actualizado con zonas y habilidades
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            prestador_actualizado = cursor.fetchone()
            if not prestador_actualizado:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["zonas"] = cursor.fetchall()

            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["habilidades"] = cursor.fetchall()

            # Publicar evento de modificación
            topic = "prestador"
            event_name = "modificacion"
            prestador_json = convert_to_json_safe(prestador_actualizado)
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
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=prestador_json
            )

            return {"detail": f"Habilidad {id_habilidad} agregada al prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


#Eliminar habilidad del prestador
@router.delete("/{prestador_id}/habilidades", summary="Quitar habilidad a prestador")
def remove_habilidad_from_prestador(
    prestador_id: int,
    id_habilidad: int = Body(..., embed=True),
    current_user: dict = Depends(require_admin_or_prestador_role)
):
    try:
        with get_connection() as (cursor, conn):
            # validar solicitudes activas
            chequear_pedidos_activos_por_habilidad(prestador_id, id_habilidad, cursor)
            
            cursor.execute(
                "DELETE FROM prestador_habilidad WHERE id_prestador = %s AND id_habilidad = %s",
                (prestador_id, id_habilidad)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Relación no encontrada")

            # Obtener prestador actualizado con zonas y habilidades
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            prestador_actualizado = cursor.fetchone()
            if not prestador_actualizado:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["zonas"] = cursor.fetchall()

            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            prestador_actualizado["habilidades"] = cursor.fetchall()

            # Publicar evento de modificación
            topic = "prestador"
            event_name = "modificacion"
            prestador_json = convert_to_json_safe(prestador_actualizado)
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
                messageId=str(event_id),
                timestamp=timestamp,
                topic=topic,
                event_name=event_name,
                payload=prestador_json
            )

            return {"detail": f"Habilidad {id_habilidad} quitada del prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/habilidad/{id_habilidad}", response_model=List[PrestadorOut], summary="Listar prestadores por habilidad")
def get_prestadores_by_habilidad(
    id_habilidad: int,
    current_user: dict = Depends(require_admin_role)
):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("""
                SELECT p.*
                FROM prestador p
                INNER JOIN prestador_habilidad ph ON p.id = ph.id_prestador
                WHERE ph.id_habilidad = %s
            """, (id_habilidad,))
            prestadores = cursor.fetchall()
            # Para cada prestador, obtener sus zonas y habilidades (con nombre de rubro)
            for prestador in prestadores:
                # Zonas
                cursor.execute("""
                    SELECT z.id, z.nombre
                    FROM zona z
                    INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                    WHERE pz.id_prestador = %s
                """, (prestador["id"],))
                prestador["zonas"] = cursor.fetchall()
                # Habilidades con nombre de rubro
                cursor.execute("""
                    SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                    FROM habilidad h
                    INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                    INNER JOIN rubro r ON h.id_rubro = r.id
                    WHERE ph.id_prestador = %s
                """, (prestador["id"],))
                prestador["habilidades"] = cursor.fetchall()
            return prestadores
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))