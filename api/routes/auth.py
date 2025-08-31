from fastapi import APIRouter, HTTPException, status
from api.schemas.prestador import PrestadorCreate, PrestadorOut
from api.core.database import get_connection
from api.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# REGISTER
@router.post("/register", response_model=PrestadorOut)
def register(prestador: PrestadorCreate):
    with get_connection() as (cursor, conn):
        cursor = conn.cursor(dictionary=True)
        # verificar si ya existe el email
        cursor.execute("SELECT * FROM prestador WHERE email = %s", (prestador.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email ya registrado")

        hashed_pw = get_password_hash(prestador.password)

        # hacer que antes vaya a buscar las zonas registradas para obtener el id_zona en vez de direccion?
        cursor.execute("SELECT id FROM zona WHERE id = %s", (prestador.id_zona,))
        zona = cursor.fetchone()
        if not zona:
            raise HTTPException(status_code=400, detail="id_zona inexistente")
        id_zona = zona["id"]

        cursor.execute(
            "INSERT INTO prestador (nombre, apellido, direccion, id_zona, email, password, telefono) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (prestador.nombre, prestador.apellido, prestador.direccion, id_zona, prestador.email, hashed_pw, prestador.telefono)
        )
        conn.commit()

        user_id = cursor.lastrowid

    return PrestadorOut(id=user_id, nombre=prestador.nombre, apellido=prestador.apellido, direccion=prestador.direccion, email=prestador.email, telefono=prestador.telefono, id_zona=id_zona)

# LOGIN
@router.post("/login")
def login(email: str, password: str):
    with get_connection() as (cursor, conn):

        cursor.execute("SELECT * FROM prestador WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user or not verify_password(password, user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

        access_token = create_access_token({"sub": str(user["id"])})
        return {"access_token": access_token, "token_type": "bearer"}
