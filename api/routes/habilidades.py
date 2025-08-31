from fastapi import APIRouter, HTTPException
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.habilidad import HabilidadCreate, HabilidadUpdate, HabilidadOut

router = APIRouter(prefix="/habilidades", tags=["Habilidades"])

# Crear habilidad
@router.post("/", response_model=HabilidadOut, summary="Crear habilidad")
def create_habilidad(habilidad: HabilidadCreate):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "INSERT INTO habilidad (nombre, descripcion, id_rubro) VALUES (%s, %s, %s)",
                (habilidad.nombre, habilidad.descripcion, habilidad.id_rubro)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return {
                "id": new_id,
                "nombre": habilidad.nombre,
                "descripcion": habilidad.descripcion,
                "id_rubro": habilidad.id_rubro
            }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Listar habilidades
@router.get("/", response_model=List[HabilidadOut], summary="Listar habilidades")
def list_habilidades(nombre: str = None, id_rubro: int = None):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor(dictionary=True)
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


# Actualizar habilidad
@router.put("/{habilidad_id}", response_model=HabilidadOut, summary="Actualizar habilidad")
def update_habilidad(habilidad_id: int, habilidad: HabilidadUpdate):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor(dictionary=True)

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
            return cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar habilidad
@router.delete("/{habilidad_id}", summary="Eliminar habilidad")
def delete_habilidad(habilidad_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM habilidad WHERE id = %s", (habilidad_id,))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Habilidad no encontrada")

            return {"detail": "Habilidad eliminada correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
