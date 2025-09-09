# routes/prestadores.py
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional
from mysql.connector import Error
from core.database import get_connection
from schemas.prestador import PrestadorCreate, PrestadorUpdate, PrestadorOut
from core.security import get_current_user

router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

# Listar todos con filtros opcionales
@router.get("/", response_model=List[PrestadorOut],
            summary="Listar prestadores",
            description="Obtiene una lista de prestadores filtrando opcionalmente por nombre, apellido, email, teléfono, dirección o zona mediante parámetro.")
def list_prestadores(
    nombre: Optional[str] = None,
    apellido: Optional[str] = None,
    email: Optional[str] = None,
    telefono: Optional[str] = None,
    direccion: Optional[str] = None,
    id_zona: Optional[int] = None,
    dni: Optional[str] = None,
    activo: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    try:        
        with get_connection() as (cursor, conn):
            query = "SELECT * FROM prestador WHERE 1 = 1"
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
            if dni:
                query += " AND dni LIKE %s"
                params.append(f"%{dni}%")
            if activo is not None:
                query += " AND activo = %s"
                params.append(activo)

            cursor.execute(query, tuple(params))
            prestadores = cursor.fetchall()

            # Para cada prestador, obtener sus zonas y habilidades (con nombre de rubro)
            for prestador in prestadores:
                # Zonas
                cursor.execute("""
                    SELECT z.id, z.nombre
                    FROM zona z
                    INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                    WHERE pz.id_prestador = %s
                """, (prestador["id"],))
                prestador["zonas"] = cursor.fetchall()
                # Habilidades con nombre de rubro
                cursor.execute("""
                    SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                    FROM habilidad h
                    INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                    INNER JOIN rubro r ON h.id_rubro = r.id
                    WHERE ph.id_prestador = %s
                """, (prestador["id"],))
                prestador["habilidades"] = cursor.fetchall()
            return prestadores
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Obtener un prestador por ID
@router.get("/{prestador_id}", response_model=PrestadorOut)
def get_prestador(prestador_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("SELECT * FROM prestador WHERE id = %s", (prestador_id,))
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")
            
            # Obtener zonas del prestador
            cursor.execute("""
                SELECT z.id, z.nombre
                FROM zona z
                INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                WHERE pz.id_prestador = %s
            """, (prestador_id,))
            zonas = cursor.fetchall()
            result["zonas"] = zonas
            
            # Obtener habilidades del prestador con nombre de rubro
            cursor.execute("""
                SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                FROM habilidad h
                INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                INNER JOIN rubro r ON h.id_rubro = r.id
                WHERE ph.id_prestador = %s
            """, (prestador_id,))
            habilidades = cursor.fetchall()
            result["habilidades"] = habilidades

            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar un prestador
@router.patch("/{prestador_id}", response_model=PrestadorOut)
def update_prestador(prestador_id: int, prestador: PrestadorUpdate, current_user: dict = Depends(get_current_user)):
    try:
        if current_user["role"] != "prestador":
            raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso")
        
        with get_connection() as (cursor, conn):
            
            fields = []
            values = []

            for key, value in prestador.dict(exclude_unset=True).items():
                fields.append(f"{key}=%s")
                values.append(value)

            if not fields:
                raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

            values.append(prestador_id)
            query = f"UPDATE prestador SET {', '.join(fields)} WHERE id=%s"
            cursor.execute(query, tuple(values))
            conn.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")

            cursor.execute("SELECT * FROM prestador WHERE id=%s", (prestador_id,))
            result = cursor.fetchone()
            return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Eliminar un prestador
@router.delete("/{prestador_id}")
def delete_prestador(prestador_id: int, current_user: dict = Depends(get_current_user)):
    try:
        if current_user["role"] != "prestador":
            raise HTTPException(status_code=403, detail="No tienes permisos para acceder a este recurso")
        
        with get_connection() as (cursor, conn):
            # Baja lógica: actualizar campo activo a False
            cursor.execute("UPDATE prestador SET activo = %s WHERE id=%s", (False, prestador_id))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Prestador no encontrado")
            return {"detail": f"Prestador {prestador_id} dado de baja correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Agregar zona al prestador
@router.post("/{prestador_id}/zonas", summary="Agregar zona a prestador")
def add_zona_to_prestador(
    prestador_id: int,
    id_zona: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO prestador_zona (id_prestador, id_zona) VALUES (%s, %s)",
                (prestador_id, id_zona)
            )
            conn.commit()
            return {"detail": f"Zona {id_zona} agregada al prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

#Eliminar zona del prestador
@router.delete("/{prestador_id}/zonas", summary="Quitar zona a prestador")
def remove_zona_from_prestador(
    prestador_id: int,
    id_zona: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM prestador_zona WHERE id_prestador = %s AND id_zona = %s",
                (prestador_id, id_zona)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Relación no encontrada")
            return {"detail": f"Zona {id_zona} quitada del prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

#Listar prestadores por zona
@router.get("/zona/{id_zona}", response_model=List[PrestadorOut], summary="Listar prestadores por zona")
def get_prestadores_by_zona(
    id_zona: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("""
                SELECT p.*
                FROM prestador p
                INNER JOIN prestador_zona pz ON p.id = pz.id_prestador
                WHERE pz.id_zona = %s
            """, (id_zona,))
            prestadores = cursor.fetchall()
            # Para cada prestador, obtener sus zonas y habilidades (con nombre de rubro)
            for prestador in prestadores:
                # Zonas
                cursor.execute("""
                    SELECT z.id, z.nombre
                    FROM zona z
                    INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                    WHERE pz.id_prestador = %s
                """, (prestador["id"],))
                prestador["zonas"] = cursor.fetchall()
                # Habilidades con nombre de rubro
                cursor.execute("""
                    SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                    FROM habilidad h
                    INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                    INNER JOIN rubro r ON h.id_rubro = r.id
                    WHERE ph.id_prestador = %s
                """, (prestador["id"],))
                prestador["habilidades"] = cursor.fetchall()
            return prestadores
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

#Agregar habilidad al prestador
@router.post("/{prestador_id}/habilidades", summary="Agregar habilidad a prestador")
def add_habilidad_to_prestador(
    prestador_id: int,
    id_habilidad: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO prestador_habilidad (id_prestador, id_habilidad) VALUES (%s, %s)",
                (prestador_id, id_habilidad)
            )
            conn.commit()
            return {"detail": f"Habilidad {id_habilidad} agregada al prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

#Eliminar habilidad del prestador
@router.delete("/{prestador_id}/habilidades", summary="Quitar habilidad a prestador")
def remove_habilidad_from_prestador(
    prestador_id: int,
    id_habilidad: int = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_connection() as (cursor, conn):
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM prestador_habilidad WHERE id_prestador = %s AND id_habilidad = %s",
                (prestador_id, id_habilidad)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Relación no encontrada")
            return {"detail": f"Habilidad {id_habilidad} quitada del prestador {prestador_id}"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/habilidad/{id_habilidad}", response_model=List[PrestadorOut], summary="Listar prestadores por habilidad")
def get_prestadores_by_habilidad(
    id_habilidad: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        with get_connection() as (cursor, conn):
            cursor.execute("""
                SELECT p.*
                FROM prestador p
                INNER JOIN prestador_habilidad ph ON p.id = ph.id_prestador
                WHERE ph.id_habilidad = %s
            """, (id_habilidad,))
            prestadores = cursor.fetchall()
            # Para cada prestador, obtener sus zonas y habilidades (con nombre de rubro)
            for prestador in prestadores:
                # Zonas
                cursor.execute("""
                    SELECT z.id, z.nombre
                    FROM zona z
                    INNER JOIN prestador_zona pz ON z.id = pz.id_zona
                    WHERE pz.id_prestador = %s
                """, (prestador["id"],))
                prestador["zonas"] = cursor.fetchall()
                # Habilidades con nombre de rubro
                cursor.execute("""
                    SELECT h.id, h.nombre, h.descripcion, h.id_rubro, r.nombre AS nombre_rubro
                    FROM habilidad h
                    INNER JOIN prestador_habilidad ph ON h.id = ph.id_habilidad
                    INNER JOIN rubro r ON h.id_rubro = r.id
                    WHERE ph.id_prestador = %s
                """, (prestador["id"],))
                prestador["habilidades"] = cursor.fetchall()
            return prestadores
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

# Crear un prestador. No se usa hasta la segunda entrega.
# @router.post("/", response_model=PrestadorOut)
# def create_prestador(prestador: PrestadorCreate):
#     try:
#         conn = get_connection()
#         
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