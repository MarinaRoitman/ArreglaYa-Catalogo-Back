from fastapi import APIRouter, HTTPException, Depends
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.zona import ZonaCreate, ZonaUpdate, ZonaOut
from core.security import get_current_user

router = APIRouter(prefix="/zonas", tags=["Zonas"])

@router.post("/", response_model=ZonaOut, summary="Crear zona")
def create_zona(zona: ZonaCreate):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor(dictionary=True)
            cursor.execute("INSERT INTO zona (nombre) VALUES (%s)", (zona.nombre,))
            conn.commit()
            new_id = cursor.lastrowid
            return {"id": new_id, "nombre": zona.nombre}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ZonaOut], summary="Listar zonas")
def list_zonas(nombre: str = None):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor(dictionary=True)
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, nombre FROM zona WHERE id = %s", (zona_id,))
            zona = cursor.fetchone()
            if not zona:
                raise HTTPException(status_code=404, detail="Zona no encontrada")
            return zona
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{zona_id}", response_model=ZonaOut, summary="Modificar zona")
def update_zona(zona_id: int, zona: ZonaUpdate):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor(dictionary=True)
            fields = []
            values = []
            if zona.nombre is not None:
                fields.append("nombre = %s")
                values.append(zona.nombre)
            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
            values.append(zona_id)
            query = f"UPDATE zona SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Zona no encontrada")
            cursor.execute("SELECT id, nombre FROM zona WHERE id = %s", (zona_id,))
            return cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{zona_id}", summary="Eliminar zona")
def delete_zona(zona_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM zona WHERE id = %s", (zona_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Zona no encontrada")
            return {"detail": "Zona eliminada correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))