from fastapi import APIRouter, HTTPException, status
from schemas.prestador import PrestadorCreate, PrestadorOut
from core.database import get_connection
from core.security import verify_password, create_access_token
from fastapi import Body, Depends
from schemas.auth import LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

# REGISTER
@router.post("/register", response_model=PrestadorOut)
def register(prestador: PrestadorCreate):
    with get_connection() as (cursor, conn):
        # verificar si ya existe el email
        cursor.execute("SELECT * FROM prestador WHERE email = %s AND activo = 1", (prestador.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email ya registrado")

        cursor.execute(
            "INSERT INTO prestador (nombre, apellido, direccion, email, password, telefono, dni) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (prestador.nombre, prestador.apellido, prestador.direccion, prestador.email, prestador.password, prestador.telefono, prestador.dni)
        )
        conn.commit()

        user_id = cursor.lastrowid

    return PrestadorOut(id=user_id, nombre=prestador.nombre, apellido=prestador.apellido, direccion=prestador.direccion, email=prestador.email, telefono=prestador.telefono, dni=prestador.dni, activo=True)

@router.post("/login")
def login(credentials: LoginRequest = Body(...)):
    with get_connection() as (cursor, conn):

        cursor.execute("SELECT * FROM prestador WHERE email = %s AND activo = 1", (credentials.email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

        access_token = create_access_token({"sub": str(user["id"]), "role": "prestador"})
        return {"access_token": access_token, "token_type": "bearer"}
