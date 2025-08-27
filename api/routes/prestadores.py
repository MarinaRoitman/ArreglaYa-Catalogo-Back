from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from mysql.connector import Error
from api.core.database import conn
from api.schemas.prestador import PrestadorCreate, PrestadorUpdate, PrestadorOut

router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

# Listar todos con filtros opcionales
@router.get("/", response_model=List[PrestadorOut])
def list_prestadores(
    nombre: Optional[str] = None,
    estado: Optional[str] = None,
    calificacion: Optional[float] = None,
    zona: Optional[str] = None,
    precio_por_hora: Optional[float] = None,
    especialidad: Optional[str] = None,
):
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM prestadores WHERE 1=1"
        params = []

        if nombre:
            query += " AND nombre LIKE %s"
            params.append(f"%{nombre}%")
        if estado:
            query += " AND estado = %s"
            params.append(estado)
        if calificacion:
            query += " AND calificacion >= %s"
            params.append(calificacion)
        if zona:
            query += " AND zona LIKE %s"
            params.append(f"%{zona}%")
        if precio_por_hora:
            query += " AND precio_por_hora <= %s"
            params.append(precio_por_hora)
        if especialidad:
            query += " AND especialidad LIKE %s"
            params.append(f"%{especialidad}%")

        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Crear un prestador
@router.post("/", response_model=PrestadorOut)
def create_prestador(prestador: PrestadorCreate):
    try:
        cursor = conn.cursor(dictionary=True)
        query = """INSERT INTO prestadores 
                   (nombre, email, direccion, telefono, estado, calificacion, zona, precio_por_hora, especialidad) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        values = (
            prestador.nombre, prestador.email, prestador.direccion,
            prestador.telefono, prestador.estado, prestador.calificacion,
            prestador.zona, prestador.precio_por_hora, prestador.especialidad
        )
        cursor.execute(query, values)
        conn.commit()
        new_id = cursor.lastrowid
        return { "id": new_id, **prestador.dict() }
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Actualizar un prestador
@router.patch("/{prestador_id}", response_model=PrestadorOut)
def update_prestador(prestador_id: int, prestador: PrestadorUpdate):
    try:
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

        cursor.execute("SELECT * FROM prestadores WHERE id=%s", (prestador_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Prestador no encontrado")
        return result
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))


# Eliminar un prestador
@router.delete("/{prestador_id}")
def delete_prestador(prestador_id: int):
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prestadores WHERE id=%s", (prestador_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Prestador no encontrado")
        return {"detail": f"Prestador {prestador_id} eliminado correctamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
router = APIRouter(prefix="/prestadores", tags=["Prestadores"])

@router.post("/", response_model=PrestadorOut)
def crear_prestador(prestador: PrestadorCreate, db: Session = Depends(get_db)):
    nuevo = Prestador(**prestador.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/", response_model=list[PrestadorOut])
def listar_prestadores(db: Session = Depends(get_db)):
    return db.query(Prestador).all()

@router.get("/{prestador_id}", response_model=PrestadorOut)
def obtener_prestador(prestador_id: int, db: Session = Depends(get_db)):
    prestador = db.query(Prestador).get(prestador_id)
    if not prestador:
        raise HTTPException(status_code=404, detail="Prestador no encontrado")
    return prestador
"""