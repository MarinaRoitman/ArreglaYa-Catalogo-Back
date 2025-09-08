from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.notificacion import NotificacionCreate, NotificacionUpdate, NotificacionOut
from core.security import get_current_user

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])

# Listar todas las notificaciones
@router.get("/", response_model=List[NotificacionOut])
def list_notificaciones(current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("SELECT * FROM notificacion")
            notificaciones = cursor.fetchall()
            return notificaciones
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener notificación por ID
@router.get("/{notificacion_id}", response_model=NotificacionOut)
def get_notificacion(notificacion_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("SELECT * FROM notificacion WHERE id = %s", (notificacion_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Notificación no encontrada")
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Crear notificación
@router.post("/", response_model=NotificacionOut)
def create_notificacion(notificacion: NotificacionCreate, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            
            query = """
                INSERT INTO notificacion (titulo, mensaje, visible, id_pedido, fecha)
                VALUES (%s, %s, %s, %s, NOW())
            """
            values = (
                notificacion.titulo,
                notificacion.mensaje,
                notificacion.visible,
                notificacion.id_pedido
            )
            cursor.execute(query, values)
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM notificacion WHERE id = %s", (new_id,))
            result = cursor.fetchone()
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Modificar notificación
@router.patch("/{notificacion_id}", response_model=NotificacionOut)
def update_notificacion(notificacion_id: int, notificacion: NotificacionUpdate, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            
            fields = []
            values = []
            for key, value in notificacion.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)
            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")
            values.append(notificacion_id)
            query = f"UPDATE notificacion SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Notificación no encontrada")
            cursor.execute("SELECT * FROM notificacion WHERE id=%s", (notificacion_id,))
            result = cursor.fetchone()
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar notificación
@router.delete("/{notificacion_id}")
def delete_notificacion(notificacion_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notificacion WHERE id=%s", (notificacion_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Notificación no encontrada")
            return {"detail": f"Notificación {notificacion_id} eliminada correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))