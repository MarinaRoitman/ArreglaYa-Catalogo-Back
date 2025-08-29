# routes/usuarios.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from mysql.connector import Error
from api.core.database import get_connection
from api.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Listar todos con filtros opcionales
@router.get("/", response_model=List[UsuarioOut])
def list_usuarios(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    direccion: Optional[str] = None,
):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM usuarios WHERE 1=1"
        params = []

        if nombre:
            query += " AND nombre LIKE %s"
            params.append(f"%{nombre}%")
        if apellido:
            query += " AND apellido LIKE %s"
            params.append(f"%{apellido}%")
        if direccion:
            query += " AND direccion LIKE %s"
            params.append(f"%{direccion}%")

        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Crear un usuario
@router.post("/", response_model=UsuarioOut)
def create_usuario(usuario: UsuarioCreate):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """INSERT INTO usuarios 
                   (nombre, apellido, direccion) 
                   VALUES (%s, %s, %s)"""
        values = (usuario.nombre, usuario.apellido, usuario.direccion)
        cursor.execute(query, values)
        conn.commit()
        new_id = cursor.lastrowid
        return { "id": new_id, **usuario.dict() }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Obtener un usuario por ID
@router.get("/{usuario_id}", response_model=UsuarioOut)
def get_usuario(usuario_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (usuario_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Actualizar un usuario
@router.patch("/{usuario_id}", response_model=UsuarioOut)
def update_usuario(usuario_id: int, usuario: UsuarioUpdate):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        fields = []
        values = []

        for key, value in usuario.dict(exclude_unset=True).items():
            fields.append(f"{key}=%s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

        values.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(fields)} WHERE id=%s"
        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cursor.execute("SELECT * FROM usuarios WHERE id=%s", (usuario_id,))
        result = cursor.fetchone()
        return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar un usuario
@router.delete("/{usuario_id}")
def delete_usuario(usuario_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id=%s", (usuario_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"detail": f"Usuario {usuario_id} eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))