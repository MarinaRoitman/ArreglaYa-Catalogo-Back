import decimal
from fastapi import APIRouter, HTTPException, status
from schemas.prestador import PrestadorCreate, PrestadorOut
from core.database import get_connection
from core.security import verify_password, create_access_token, get_password_hash
from fastapi import Body, Depends
from schemas.auth import LoginRequest
import json
from datetime import datetime, timezone
from core.events import publish_event

router = APIRouter(prefix="/auth", tags=["Auth"])

def _convert_to_json_safe(obj):
    if isinstance(obj, dict):
        return {k: _convert_to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_to_json_safe(v) for v in obj]
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.replace(tzinfo=timezone.utc).isoformat()
    return obj

def _row_to_dict(cursor, row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    # cursor.description tiene (name, type_code, ...) por columna
    return {desc[0]: row[idx] for idx, desc in enumerate(cursor.description)}

# REGISTER
@router.post("/register", response_model=PrestadorOut)
def register(prestador: PrestadorCreate):
    with get_connection() as (cursor, conn):
        # Verificar si ya existe email o dni
        cursor.execute("SELECT * FROM prestador WHERE (email = %s OR dni = %s) AND activo = 1", (prestador.email, prestador.dni))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email o DNI ya registrado")

        # Hashear la contraseña ANTES de insertarla
        hashed_password = get_password_hash(prestador.password)

        cursor.execute(
            "INSERT INTO prestador (nombre, apellido, direccion, email, password, telefono, dni) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (prestador.nombre, prestador.apellido, prestador.direccion,
             prestador.email, hashed_password, prestador.telefono, prestador.dni)
        )
        conn.commit()
        user_id = cursor.lastrowid

        # Recuperar usuario
        cursor.execute(
            "SELECT id, nombre, apellido, direccion, email, telefono, dni, activo, foto "
            "FROM prestador WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=500, detail="Error al recuperar prestador creado")

        row_dict = _row_to_dict(cursor, row)
        row_dict.setdefault("habilidades", [])
        row_dict.setdefault("zonas", [])

        prestador_json = _convert_to_json_safe(row_dict)
        payload_str = json.dumps(prestador_json, ensure_ascii=False)

        # Publicar evento de alta
        channel = "catalogue.prestador.alta"
        event_name = "alta_prestador"

        cursor.execute(
            "INSERT INTO eventos_publicados (channel, event_name, payload) VALUES (%s, %s, %s)",
            (channel, event_name, payload_str)
        )
        conn.commit()

        # Enviar evento al Core
        event_id = cursor.lastrowid
        cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
        created_at_value = cursor.fetchone()
        timestamp = datetime.now(timezone.utc).isoformat()

        publish_event(
            messageId=str(event_id),
            timestamp=timestamp,
            channel=channel,
            eventName=event_name,
            payload=prestador_json
        )

        return row_dict


@router.post("/login")
def login(credentials: LoginRequest = Body(...)):
    with get_connection() as (cursor, conn):
        # Buscar en prestador
        cursor.execute("SELECT * FROM prestador WHERE email = %s AND activo = 1", (credentials.email,))
        user = cursor.fetchone()

        if user and verify_password(credentials.password, user["password"]):
            access_token = create_access_token({"sub": str(user["id"]), "role": "prestador"})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "rol": "prestador"
            }

        # Buscar en admin
        cursor.execute("SELECT * FROM admin WHERE email = %s AND activo = 1", (credentials.email,))
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin and verify_password(credentials.password, admin["password"]):
            access_token = create_access_token({"sub": str(admin["email"]), "role": "admin"})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "rol": "admin"
            }

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
