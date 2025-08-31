# routes/prestadores.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from mysql.connector import Error
from ..core.database import get_connection
from ..schemas.prestador import PrestadorCreate, PrestadorUpdate, PrestadorOut

router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

# Listar todos con filtros opcionales
@router.get("/", response_model=List[PrestadorOut],
            summary="Listar prestadores",
            description="Obtiene una lista de prestadores filtrando opcionalmente por nombre, apellido, email, teléfono, dirección o zona.")
def list_prestadores(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    direccion: Optional[str] = None,
    id_zona: Optional[int] = None
):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM prestadores where 1 = 1"
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
        if telefono:
            query += " AND telefono LIKE %s"
            params.append(f"%{telefono}%")
        if direccion:
            query += " AND direccion LIKE %s"
            params.append(f"%{direccion}%")
        if id_zona:
            query += " AND id_zona = %s"
            params.append(id_zona)

        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Crear un prestador. No se usa hasta la segunda entrega.
# @router.post("/", response_model=PrestadorOut)
# def create_prestador(prestador: PrestadorCreate):
#     try:
#         conn = get_connection()
#         cursor = conn.cursor(dictionary=True)
#         query = """INSERT INTO prestadores 
#                    (nombre, apellido, email, telefono, direccion, id_zona) 
#                    VALUES (%s, %s, %s, %s, %s, %s)"""
#         values = (
#             prestador.nombre, prestador.apellido, prestador.email,
#             prestador.telefono, prestador.direccion, prestador.id_zona
#         )
#         cursor.execute(query, values)
#         conn.commit()
#         new_id = cursor.lastrowid
#         return { "id": new_id, **prestador.dict() }
#     except Error as e:
#         raise HTTPException(status_code=500, detail=str(e))


# Obtener un prestador por ID
@router.get("/{prestador_id}", response_model=PrestadorOut)
def get_prestador(prestador_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM prestadores WHERE id = %s", (prestador_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Prestador no encontrado")
        return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Actualizar un prestador
@router.patch("/{prestador_id}", response_model=PrestadorOut)
def update_prestador(prestador_id: int, prestador: PrestadorUpdate):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        fields = []
        values = []

        for key, value in prestador.dict(exclude_unset=True).items():
            fields.append(f"{key}=%s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

        values.append(prestador_id)
        query = f"UPDATE prestadores SET {', '.join(fields)} WHERE id=%s"
        cursor.execute(query, tuple(values))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Prestador no encontrado")

        cursor.execute("SELECT * FROM prestadores WHERE id=%s", (prestador_id,))
        result = cursor.fetchone()
        return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar un prestador
@router.delete("/{prestador_id}")
def delete_prestador(prestador_id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prestadores WHERE id=%s", (prestador_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Prestador no encontrado")
        return {"detail": f"Prestador {prestador_id} eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
