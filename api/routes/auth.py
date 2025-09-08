from fastapi import APIRouter, HTTPException, status
from schemas.prestador import PrestadorCreate, PrestadorOut
from core.database import get_connection
from core.security import get_password_hash, verify_password, create_access_token
from fastapi import Body, Depends
from schemas.auth import LoginRequest


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
            "INSERT INTO prestador (nombre, apellido, direccion, id_zona, email, password, telefono, dni) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (prestador.nombre, prestador.apellido, prestador.direccion, id_zona, prestador.email, hashed_pw, prestador.telefono, prestador.dni)
        )
        conn.commit()

        user_id = cursor.lastrowid

    return PrestadorOut(id=user_id, nombre=prestador.nombre, apellido=prestador.apellido, direccion=prestador.direccion, email=prestador.email, telefono=prestador.telefono, id_zona=id_zona, dni=prestador.dni, activo=True)

@router.post("/login")
def login(credentials: LoginRequest = Body(...)):
    with get_connection() as (cursor, conn):

        cursor.execute("SELECT * FROM prestador WHERE email = %s", (credentials.email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

        access_token = create_access_token({"sub": str(user["id"]), "role": "prestador"})
        return {"access_token": access_token, "token_type": "bearer"}
