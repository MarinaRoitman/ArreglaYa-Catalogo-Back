import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut
from core.security import require_admin_role, require_admin_or_prestador_role, require_internal_or_admin

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Listar todos con filtros opcionales (requiere JWT)
@router.get("/", response_model=List[UsuarioOut])
def list_usuarios(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    dni: Optional[str] = None,
    estado_pri: Optional[str] = None,
    ciudad_pri: Optional[str] = None,
    telefono: Optional[str] = None,
    id_usuario: Optional[int] = None,
    current_user: dict = Depends(require_internal_or_admin)
):
    try:
        with get_connection() as (cursor, conn):
            query = """SELECT id, nombre, apellido, dni, telefono, activo, foto,
                      estado_pri, ciudad_pri, calle_pri, numero_pri, piso_pri, departamento_pri,
                      estado_sec, ciudad_sec, calle_sec, numero_sec, piso_sec, departamento_sec, id_usuario
                      FROM usuario WHERE 1=1"""
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
            if estado_pri:
                query += " AND estado_pri LIKE %s"
                params.append(f"%{estado_pri}%")
            if ciudad_pri:
                query += " AND ciudad_pri LIKE %s"
                params.append(f"%{ciudad_pri}%")
            if telefono:
                query += " AND telefono LIKE %s"
                params.append(f"%{telefono}%")
            if id_usuario:
                query += " AND id_usuario = %s"
                params.append(id_usuario)

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=UsuarioOut)
def create_usuario(usuario: UsuarioCreate, current_user: dict = Depends(require_internal_or_admin)):
    try:
        with get_connection() as (cursor, conn):
            # Preparar campos y valores dinámicamente
            campos = [
                "nombre", "apellido", "dni", "telefono", "id_usuario",
                "estado_pri", "ciudad_pri", "calle_pri", "numero_pri", "piso_pri", "departamento_pri",
                "estado_sec", "ciudad_sec", "calle_sec", "numero_sec", "piso_sec", "departamento_sec"
            ]
            valores = [
                usuario.nombre, usuario.apellido, usuario.dni, usuario.telefono, 
                usuario.id_usuario,
                usuario.estado_pri, usuario.ciudad_pri, usuario.calle_pri, 
                usuario.numero_pri, usuario.piso_pri, usuario.departamento_pri,
                usuario.estado_sec, usuario.ciudad_sec, usuario.calle_sec,
                usuario.numero_sec, usuario.piso_sec, usuario.departamento_sec
            ]

            # Si hay foto, agregar el campo foto
            if usuario.foto is not None:
                campos.append("foto")
                valores.append(usuario.foto)

            # Construir la consulta dinámicamente
            campos_str = ", ".join(campos)
            placeholders = ", ".join(["%s"] * len(campos))
            query = f"""INSERT INTO usuario ({campos_str})
                       VALUES ({placeholders})"""
            values = tuple(valores)

            cursor.execute(query, values)
            conn.commit()
            new_id = cursor.lastrowid

            # recuperar fila creada (incluye foto por defecto si no se envió)
            cursor.execute("""
                SELECT id, nombre, apellido, dni, telefono, activo, id_usuario, foto,
                estado_pri, ciudad_pri, calle_pri, numero_pri, piso_pri, departamento_pri,
                estado_sec, ciudad_sec, calle_sec, numero_sec, piso_sec, departamento_sec
                FROM usuario WHERE id = %s""", (new_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Error al recuperar usuario creado")
            return row
    except Error as e:
        logging.exception(f"Error creando usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{usuario_id}", response_model=UsuarioOut)
def get_usuario(usuario_id: int, current_user: dict = Depends(require_admin_or_prestador_role)):
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
def update_usuario(
    usuario_id: int,
    usuario: UsuarioUpdate,
    current_user: dict = Depends(require_internal_or_admin)
):
    ...

    try:
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
def delete_usuario(usuario_id: int, current_user: dict = Depends(require_internal_or_admin)):  
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("UPDATE usuario SET activo = %s WHERE id=%s", (False, usuario_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return {"detail": f"Usuario {usuario_id} dado de baja correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
