# api/routes/auth.py
from fastapi import APIRouter, HTTPException, status, Body, BackgroundTasks
from schemas.prestador import PrestadorCreate, PrestadorOut
from core.database import get_connection
from core.security import get_password_hash, verify_password, create_access_token
from schemas.auth import LoginRequest
from core.events import publish_event

router = APIRouter(prefix="/auth", tags=["Auth"])

# REGISTER
@router.post("/register", response_model=PrestadorOut)
def register(prestador: PrestadorCreate, background: BackgroundTasks):
    with get_connection() as (cursor, conn):
        # verificar si ya existe el email
        cursor.execute("SELECT * FROM prestador WHERE email = %s", (prestador.email,))
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

    # publicar evento en background (no bloquea la respuesta)
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
    # Modo conmutable por env: USERS_AUTH_MODE=rpc | local (default)
    import os
    mode = os.getenv("USERS_AUTH_MODE", "local").lower().strip()

    if mode == "rpc":
        # Requiere: from core.rpc import rpc_login
        resp = rpc_login(credentials.email, credentials.password, timeout_sec=3.0)
        if not resp.get("ok"):
            msg = resp.get("error", "login failed")
            code = status.HTTP_401_UNAUTHORIZED if "invalid" in msg.lower() else status.HTTP_503_SERVICE_UNAVAILABLE
            raise HTTPException(status_code=code, detail=msg)
        return {"access_token": resp["token"], "token_type": "bearer"}

    # ---- fallback local (tu implementación actual) ----
    with get_connection() as (cursor, conn):
        cursor.execute("SELECT * FROM prestador WHERE email = %s", (credentials.email,))
        user = cursor.fetchone()
        cursor.close(); conn.close()

        if not user or not verify_password(credentials.password, user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

        access_token = create_access_token({"sub": str(user["id"]), "role": "prestador"})
        return {"access_token": access_token, "token_type": "bearer"}
