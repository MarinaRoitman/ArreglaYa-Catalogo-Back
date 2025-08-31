from fastapi import APIRouter, HTTPException, Depends
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.zona import ZonaCreate, ZonaOut
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
def list_zonas(
    nombre: str = None
):
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