from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.calificacion import CalificacionCreate, CalificacionUpdate, CalificacionOut
from core.security import  require_admin_role, require_admin_or_prestador_role

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])


# Listar calificaciones (con filtros opcionales)
@router.get("/", response_model=List[CalificacionOut])
def list_calificaciones(
    id_prestador: Optional[int] = None,
    id_usuario: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_prestador_role)
):
    try:
        with get_connection() as (cursor, conn):
            query = "SELECT id, estrellas, descripcion, id_prestador, id_usuario FROM calificacion WHERE 1=1"
            params = []
            if id_prestador is not None:
                query += " AND id_prestador = %s"
                params.append(id_prestador)
            if id_usuario is not None:
                query += " AND id_usuario = %s"
                params.append(id_usuario)
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Obtener una calificación por ID
@router.get("/{calificacion_id}", response_model=CalificacionOut)
def get_calificacion(calificacion_id: int, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute(
                "SELECT id, estrellas, descripcion, id_prestador, id_usuario FROM calificacion WHERE id = %s",
                (calificacion_id,),
            )
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Calificación no encontrada")
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Crear una calificación
@router.post("/", response_model=CalificacionOut)
def create_calificacion(calificacion: CalificacionCreate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            # Validar existencia de prestador
            cursor.execute("SELECT id FROM prestador WHERE id = %s", (calificacion.id_prestador,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            # Validar existencia de usuario
            cursor.execute("SELECT id FROM usuario WHERE id = %s", (calificacion.id_usuario,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            query = """INSERT INTO calificacion (estrellas, descripcion, id_prestador, id_usuario, id_calificacion)
                       VALUES (%s, %s, %s, %s, %s)"""
            values = (
                calificacion.estrellas,
                calificacion.descripcion,
                calificacion.id_prestador,
                calificacion.id_usuario,
                calificacion.id_calificacion
            )
            cursor.execute(query, values)
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, estrellas, descripcion, id_prestador, id_usuario, id_calificacion FROM calificacion WHERE id = %s",
                (new_id,),
            )
            return cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Actualizar una calificación
@router.patch("/{calificacion_id}", response_model=CalificacionOut)
def update_calificacion(calificacion_id: int, calificacion: CalificacionUpdate, current_user: dict = Depends(require_admin_or_prestador_role)):
    try:
        with get_connection() as (cursor, conn):
            fields = []
            values = []
            cursor.execute("SELECT id FROM calificacion WHERE id = %s", (calificacion_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Calificación no encontrada")

            for key, value in calificacion.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

            values.append(calificacion_id)
            query = f"UPDATE calificacion SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Calificación no encontrada")

            cursor.execute(
                "SELECT id, estrellas, descripcion, id_prestador, id_usuario, id_calificacion FROM calificacion WHERE id=%s",
                (calificacion_id,),
            )
            return cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar una calificación
@router.delete("/{calificacion_id}")
def delete_calificacion(calificacion_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("DELETE FROM calificacion WHERE id=%s", (calificacion_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Calificación no encontrada")
            return {"detail": f"Calificación {calificacion_id} eliminada correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
