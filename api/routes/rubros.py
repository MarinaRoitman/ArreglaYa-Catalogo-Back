from fastapi import APIRouter, HTTPException
from typing import List
from mysql.connector import Error
from core.database import get_connection
from schemas.rubro import RubroCreate, RubroUpdate, RubroOut

router = APIRouter(prefix="/rubros", tags=["Rubros"])

# Crear rubro
@router.post("/", response_model=RubroOut, summary="Crear rubro")
def create_rubro(rubro: RubroCreate):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("INSERT INTO rubro (nombre) VALUES (%s)", (rubro.nombre,))
            conn.commit()
            new_id = cursor.lastrowid
            return {"id": new_id, "nombre": rubro.nombre}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Listar rubros (con filtro opcional por nombre)
@router.get("/", response_model=List[RubroOut], summary="Listar rubros")
def list_rubros(nombre: str = None):
    try:
        with get_connection() as (cursor, conn):
            
            query = "SELECT id, nombre FROM rubro WHERE 1=1"
            params = []
            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{rubro_id}", response_model=RubroOut, summary="Obtener rubro por ID")
def get_rubro(rubro_id: int):
    try:
        with get_connection() as (cursor, conn):
            
            cursor.execute("SELECT id, nombre FROM rubro WHERE id = %s", (rubro_id,))
            rubro = cursor.fetchone()
            if not rubro:
                raise HTTPException(status_code=404, detail="Rubro no encontrado")
            return rubro
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar rubro
@router.patch("/{rubro_id}", response_model=RubroOut, summary="Actualizar rubro")
def update_rubro(rubro_id: int, rubro: RubroUpdate):
    try:
        with get_connection() as (cursor, conn):
            
            fields = []
            values = []
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
            return cursor.fetchone()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar rubro
@router.delete("/{rubro_id}", summary="Eliminar rubro")
def delete_rubro(rubro_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rubro WHERE id = %s", (rubro_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Rubro no encontrado")
            return {"detail": "Rubro eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))