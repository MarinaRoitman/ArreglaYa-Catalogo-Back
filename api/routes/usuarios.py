from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut
from core.security import get_current_user  

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# Listar todos con filtros opcionales (requiere JWT)
@router.get("/", response_model=List[UsuarioOut])
def list_usuarios(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    dni: Optional[str] = None,
    direccion: Optional[str] = None,
    current_user: dict = Depends(get_current_user)  
):
    try:
        with get_connection() as (cursor, conn):
            query = "SELECT id, nombre, apellido, direccion, dni FROM usuario WHERE 1=1"
            params = []

            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            if apellido:
                query += " AND apellido LIKE %s"
                params.append(f"%{apellido}%")
            if dni:
                query += " AND dni LIKE %s"
                params.append(f"%{dni}%")
            if direccion:
                query += " AND direccion LIKE %s"
                params.append(f"%{direccion}%")

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Crear un usuario (registro público → no requiere JWT)
@router.post("/", response_model=UsuarioOut)
def create_usuario(usuario: UsuarioCreate):
    try:
        with get_connection() as (cursor, conn):
            query = """INSERT INTO usuario
                       (nombre, apellido, direccion, dni) 
                       VALUES (%s, %s, %s, %s)"""
            values = (usuario.nombre, usuario.apellido, usuario.direccion, usuario.dni)
            cursor.execute(query, values)
            conn.commit()
            new_id = cursor.lastrowid
            return { "id": new_id, **usuario.dict() }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Obtener un usuario por ID (puede ser público o privado → acá lo dejo público)
@router.get("/{usuario_id}", response_model=UsuarioOut)
def get_usuario(usuario_id: int):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT * FROM usuario WHERE id = %s", (usuario_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Actualizar un usuario (requiere JWT)
@router.patch("/{usuario_id}", response_model=UsuarioOut)
def update_usuario(usuario_id: int, usuario: UsuarioUpdate, current_user: dict = Depends(get_current_user)):  # 🔒
    try:
        # Se podría validar acá que `current_user["id"] == usuario_id` o que sea admin
        if current_user["id"] != usuario_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar este usuario")
        with get_connection() as (cursor, conn):
            fields = []
            values = []

            for key, value in usuario.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

            values.append(usuario_id)
            query = f"UPDATE usuario SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            cursor.execute("SELECT * FROM usuario WHERE id=%s", (usuario_id,))
            result = cursor.fetchone()
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar un usuario (requiere JWT)
@router.delete("/{usuario_id}")
def delete_usuario(usuario_id: int, current_user: dict = Depends(get_current_user)):  
    try:
        # Se valida que el usuario solo pueda borrarse a sí mismo. (validar que sea admin?)
        if current_user["id"] != usuario_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este usuario")
        with get_connection() as (cursor, conn):
            cursor.execute("DELETE FROM usuario WHERE id=%s", (usuario_id,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return {"detail": f"Usuario {usuario_id} eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
