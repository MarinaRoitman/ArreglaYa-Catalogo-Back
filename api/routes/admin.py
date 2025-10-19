from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.admin import AdminCreate, AdminUpdate, AdminOut
from core.security import get_password_hash, require_admin_role

router = APIRouter(prefix="/admins", tags=["Admins"])

# Listar todos con filtros opcionales (solo admin)
@router.get("/", response_model=List[AdminOut])
def list_admins(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    email: Optional[str] = None,
    current_user: dict = Depends(require_admin_role)
):
    try:
        with get_connection() as (cursor, conn):
            query = "SELECT id, nombre, apellido, email, activo, id_admin, foto FROM admin WHERE 1=1"
            params = []

            if nombre:
                query += " AND nombre LIKE %s"
                params.append(f"%{nombre}%")
            if apellido:
                query += " AND apellido LIKE %s"
                params.append(f"%{apellido}%")
            if email:
                query += " AND email LIKE %s"
                params.append(f"%{email}%")

            cursor.execute(query, tuple(params))
            return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Crear un admin (solo admin)
@router.post("/", response_model=AdminOut)
def create_admin(admin: AdminCreate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            hashed_password = get_password_hash(admin.password)
            query = """INSERT INTO admin
                       (nombre, apellido, email, password, id_admin, activo, foto)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            values = (
                admin.nombre,
                admin.apellido,
                admin.email,
                hashed_password,
                admin.id_admin,
                True,
                admin.foto
            )
            cursor.execute(query, values)
            conn.commit()
            new_id = cursor.lastrowid
            return {
                "id": new_id,
                "nombre": admin.nombre,
                "apellido": admin.apellido,
                "email": admin.email,
                "activo": True,
                "id_admin": admin.id_admin,
                "foto": admin.foto
            }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener un admin por ID (solo admin)
@router.get("/{admin_id}", response_model=AdminOut)
def get_admin(admin_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT id, nombre, apellido, email, activo, id_admin, foto FROM admin WHERE id = %s", (admin_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Admin no encontrado")
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar un admin (solo admin)
@router.patch("/{admin_id}", response_model=AdminOut)
def update_admin(admin_id: int, admin: AdminUpdate, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            fields = []
            values = []

            update_data = admin.dict(exclude_unset=True)
            if 'password' in update_data and update_data['password']:
                hashed_password = get_password_hash(update_data['password'])
                fields.append("password=%s")
                values.append(hashed_password)
                del update_data['password']
                
            for key, value in admin.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

            values.append(admin_id)
            query = f"UPDATE admin SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Admin no encontrado")

            cursor.execute("SELECT id, nombre, apellido, email, activo, id_admin, foto FROM admin WHERE id=%s", (admin_id,))
            result = cursor.fetchone()
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar un admin (baja lógica, solo admin)
@router.delete("/{admin_id}")
def delete_admin(admin_id: int, current_user: dict = Depends(require_admin_role)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("UPDATE admin SET activo = %s WHERE id=%s", (False, admin_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Admin no encontrado")
            return {"detail": f"Admin {admin_id} dado de baja correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))