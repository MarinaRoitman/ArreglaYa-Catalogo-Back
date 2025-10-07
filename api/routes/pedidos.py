from datetime import datetime, timezone
from decimal import Decimal
import json
from core.events import publish_event
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.pedido import PedidoCreate, PedidoUpdate, PedidoOut
from core.security import require_admin_role, require_admin_or_prestador_role
from schemas.pedido import EstadoPedido

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# Crear pedido
@router.post("/", response_model=PedidoOut, summary="Crear pedido")
def create_pedido(pedido: PedidoCreate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            # INSERT
            query = """
                INSERT INTO pedido (estado, descripcion, tarifa, fecha, fecha_creacion, fecha_ultima_actualizacion, id_prestador, id_usuario, id_habilidad, id_pedido)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), %s, %s, %s, %s)
            """
            values = (
                pedido.estado,
                pedido.descripcion,
                pedido.tarifa,
                pedido.fecha,
                pedido.id_prestador,
                pedido.id_usuario,
                pedido.id_habilidad,
                pedido.id_pedido
            )
            cursor.execute(query, values)
            conn.commit()
            new_id = cursor.lastrowid

            # SELECT
            cursor.execute("SELECT * FROM pedido WHERE id = %s", (new_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Pedido no encontrado después de crear")
            return row

    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Listar pedidos (con filtros opcionales)
@router.get("/", response_model=List[PedidoOut], summary="Listar pedidos")
def list_pedidos(
    id_usuario: Optional[int] = None,
    id_prestador: Optional[int] = None,
    estado: Optional[str] = None,
    id_habilidad: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_prestador_role)
):
    try:
        with get_connection() as (cursor, conn):
            
            query = "SELECT * FROM pedido WHERE 1=1"
            params = []
            if id_usuario:
                query += " AND id_usuario = %s"
                params.append(id_usuario)
            if id_prestador:
                query += " AND id_prestador = %s"
                params.append(id_prestador)
            if estado:
                query += " AND estado = %s"
                params.append(estado)
            if id_habilidad:
                query += " AND id_habilidad = %s"
                params.append(id_habilidad)
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener pedido por ID
@router.get("/{pedido_id}", response_model=PedidoOut, summary="Obtener pedido por ID")
def get_pedido(pedido_id: int, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("SELECT * FROM pedido WHERE id = %s", (pedido_id,))
            pedido = cursor.fetchone()
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            return pedido
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{pedido_id}", response_model=PedidoOut, summary="Modificar pedido")
def update_pedido(pedido_id: int, pedido: PedidoUpdate, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            fields, values = [], []
            for key, value in pedido.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)
            fields.append("fecha_ultima_actualizacion=NOW()")
            values.append(pedido_id)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

            query = f"UPDATE pedido SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")

            cursor.execute("SELECT * FROM pedido WHERE id = %s", (pedido_id,))
            pedido_actualizado = cursor.fetchone()
            
            # --- Detectar tipo de evento según el nuevo estado ---
            estado = pedido.model_dump(exclude_unset=True).get("estado")
            if estado == "aprobado_por_prestador":
                channel = "catalogue.pedidos.cotizacion_enviada"
                event_name = "cotizacion_enviada"
            elif estado == "finalizado":
                channel = "catalogue.pedidos.finalizado"
                event_name = "pedido_finalizado"
            else:
                return pedido_actualizado  # no publicamos evento si no aplica

            # --- Publicar evento ---
            pedido_json = convert_to_json_safe(pedido_actualizado)
            payload = json.dumps(pedido_json, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO eventos_publicados (channel, event_name, payload) VALUES (%s, %s, %s)",
                (channel, event_name, payload)
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
                channel=channel,
                eventName=event_name,
                payload=pedido_json
            )

            return pedido_actualizado
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar pedido
@router.delete("/{pedido_id}", summary="Cancelar pedido")
def delete_pedido(pedido_id: int, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            # Obtener pedido original
            cursor.execute("SELECT * FROM pedido WHERE id = %s", (pedido_id,))
            pedido = cursor.fetchone()
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            
            # Actualizar estado a cancelado
            cursor.execute(
                "UPDATE pedido SET estado = %s, fecha_ultima_actualizacion = NOW() WHERE id = %s",
                ("cancelado", pedido_id)
            )
            conn.commit()
            
            # Obtener el pedido actualizado
            cursor.execute("SELECT * FROM pedido WHERE id = %s", (pedido_id,))
            pedido_actualizado = cursor.fetchone()
            
            # Datos del evento
            channel = "catalogue.pedidos.cancelado"
            event_name = "pedido_cancelado"

            pedido_json_safe = convert_to_json_safe(pedido_actualizado)
            payload = json.dumps(pedido_json_safe, ensure_ascii=False)

            # Insertar evento en tabla local
            insert_event_query = """
                INSERT INTO eventos_publicados (channel, event_name, payload)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_event_query, (channel, event_name, payload))
            conn.commit()

            # Obtener ID y fecha del evento
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
            
            # Publicar evento en CoreHub
            publish_event(
                messageId=str(event_id),
                timestamp=timestamp,
                channel=channel,
                eventName=event_name,
                payload=pedido_json_safe  # usar el que ya es JSON-safe
            )
            
            return {"detail": "Pedido cancelado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

def convert_to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_safe(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj