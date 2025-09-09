from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.pedido import PedidoCreate, PedidoUpdate, PedidoOut
from core.security import get_current_user
from core.security import require_prestador_role

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

# Crear pedido
@router.post("/", response_model=PedidoOut, summary="Crear pedido")
def create_pedido(pedido: PedidoCreate, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            # INSERT
            query = """
                INSERT INTO pedido (estado, descripcion, tarifa, fecha, fecha_creacion, fecha_ultima_actualizacion, id_prestador, id_usuario)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), %s, %s)
            """
            values = (
                pedido.estado,
                pedido.descripcion,
                pedido.tarifa,
                pedido.fecha,
                pedido.id_prestador,
                pedido.id_usuario
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
    current_user: dict = Depends(get_current_user)
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
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener pedido por ID
@router.get("/{pedido_id}", response_model=PedidoOut, summary="Obtener pedido por ID")
def get_pedido(pedido_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("SELECT * FROM pedido WHERE id = %s", (pedido_id,))
            pedido = cursor.fetchone()
            if not pedido:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            return pedido
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Modificar pedido
@router.patch("/{pedido_id}", response_model=PedidoOut, summary="Modificar pedido")
def update_pedido(pedido_id: int, pedido: PedidoUpdate, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            fields = []
            values = []
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
            return cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar pedido
@router.delete("/{pedido_id}", summary="Eliminar pedido")
def delete_pedido(pedido_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pedido WHERE id = %s", (pedido_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Pedido no encontrado")
            return {"detail": "Pedido eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))