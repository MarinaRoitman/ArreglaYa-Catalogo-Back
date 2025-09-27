# api/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Body, BackgroundTasks
from schemas.prestador import PrestadorCreate, PrestadorOut
from core.database import get_connection
from core.security import get_password_hash, verify_password, create_access_token
from schemas.auth import LoginRequest
from core.events import publish_event
from core.rpc import rpc_login   # ← you forgot me

router = APIRouter(prefix="/auth", tags=["Auth"])

# REGISTER
@router.post("/register", response_model=PrestadorOut)
def register(prestador: PrestadorCreate, background: BackgroundTasks):
    with get_connection() as (cursor, conn):
        cursor.execute("SELECT 1 FROM prestador WHERE email = %s", (prestador.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email ya registrado")

        hashed_pw = get_password_hash(prestador.password)
        cursor.execute(
            """
            INSERT INTO prestador (nombre, apellido, direccion, email, password, telefono, dni)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (prestador.nombre, prestador.apellido, prestador.direccion,
             prestador.email, hashed_pw, prestador.telefono, prestador.dni)
        )
        conn.commit()
        user_id = cursor.lastrowid

    # publish event in background, so your API isn’t held hostage by the bus
    payload = {
        "id": user_id,
        "nombre": prestador.nombre,
        "apellido": prestador.apellido,
        "email": prestador.email,
        "telefono": prestador.telefono,
        "dni": prestador.dni,
    }
    background.add_task(publish_event, "worker.prestador.registered", payload)

    return PrestadorOut(
        id=user_id,
        nombre=prestador.nombre,
        apellido=prestador.apellido,
        direccion=prestador.direccion,
        email=prestador.email,
        telefono=prestador.telefono,
        dni=prestador.dni,
        activo=True,
    )

@router.post("/login")
def login(credentials: LoginRequest = Body(...)):
    import os
    mode = os.getenv("USERS_AUTH_MODE", "local").strip().lower()

    if mode == "rpc":
        resp = rpc_login(credentials.email, credentials.password, timeout_sec=4.0)
        if not resp.get("ok"):
            msg = resp.get("error", "login_failed")

            # map errors to codes without psychic powers
            if "invalid" in msg.lower():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
            if "timeout" in msg.lower() or "amqp_error" in msg.lower():
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Auth service unavailable")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=msg)

        return {"access_token": resp["token"], "token_type": "bearer"}

    # Fallback: local DB auth
    with get_connection() as (cursor, _conn):
        cursor.execute("SELECT id, password FROM prestador WHERE email = %s", (credentials.email,))
        user = cursor.fetchone()

    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": str(user["id"]), "role": "prestador"})
    return {"access_token": access_token, "token_type": "bearer"}
