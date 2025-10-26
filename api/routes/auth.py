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
from passlib.context import CryptContext
import httpx

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["Auth"])

# Usar puerto 8081 para pegarle a dev, o 8080 para prod
EXTERNAL_LOGIN_URL = "http://dev.desarrollo2-usuarios.shop:8081/api/users/login"

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

@router.post("/register", response_model=PrestadorOut)
def register(prestador: PrestadorCreate):
    row_dict = prestador.model_dump()
    
    row_dict.setdefault("habilidades", [])
    row_dict.setdefault("zonas", [])
    row_dict.setdefault("activo", True) # Asumir True para el evento de alta
    row_dict.setdefault("foto", None)  # Asumir None

    prestador_json = _convert_to_json_safe(row_dict)
    payload_str = json.dumps(prestador_json, ensure_ascii=False)

    with get_connection() as (cursor, conn):
        # Publicar evento de alta
        topic = "prestador"
        event_name = "alta"

        cursor.execute(
            "INSERT INTO eventos_publicados (topic, event_name, payload) VALUES (%s, %s, %s)",
            (topic, event_name, payload_str)
        )
        conn.commit()

        # Usar el ID del evento como el ID del prestador para la respuesta
        event_id = cursor.lastrowid

        # Enviar evento al Core
        cursor.execute("SELECT created_at FROM eventos_publicados WHERE id = %s", (event_id,))
        event_row = cursor.fetchone()
        
        timestamp = None
        if event_row:
            created_at_value = event_row[0] if isinstance(event_row, tuple) else event_row.get('created_at')
            if isinstance(created_at_value, datetime):
                timestamp = created_at_value.replace(tzinfo=timezone.utc).isoformat()

        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()

        publish_event(
            message_id=str(event_id),
            timestamp=timestamp,
            topic=topic,
            event_name=event_name,
            payload=prestador_json
        )

        return row_dict


@router.post("/login")
def login(credentials: LoginRequest = Body(...)):
    # Preparamos el body para la solicitud externa
    login_data = credentials.model_dump()

    try:
        # Hacemos la llamada al servicio externo
        with httpx.Client() as client:
            response = client.post(EXTERNAL_LOGIN_URL, json=login_data)
        
        # Manejar la respuesta del servicio externo
        if response.status_code == 401:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        
        # Lanza un error si la solicitud externa falló por otra razón
        response.raise_for_status() 

        # Si llegamos acá, el login externo fue exitoso
        external_data = response.json()
        
        user_info = external_data.get("userInfo")
        if not user_info:
            raise HTTPException(status_code=500, detail="Respuesta de login externo incompleta: falta 'userInfo'")

        # Extraer datos y NORMALIZAR el rol        
        external_role = user_info.get("role", "").lower() # "prestador" o "admin"
        user_id = user_info.get("id")

        if not user_id:
             raise HTTPException(status_code=500, detail="Respuesta de login externo incompleta: falta 'id' en 'userInfo'")
        
        # Mapeo de roles
        internal_role = None
        if external_role == "prestador":
            internal_role = "prestador"
        elif "admin" in external_role:
            internal_role = "admin"
        
        if internal_role is None:
             raise HTTPException(status_code=403, detail="El rol de usuario no es compatible con esta aplicación")

        # 6. Crear token interno
        data_to_encode = {
            "sub": str(user_id),
            "role": internal_role 
        }
        internal_access_token = create_access_token(data=data_to_encode)

        # El frontend usará este internal_access_token para todas las peticiones
        return {
            "access_token": internal_access_token,
            "token_type": "bearer",
            "rol": internal_role
        }

    except httpx.RequestError as exc:
        # Error de conexión con el servicio de login
        raise HTTPException(status_code=503, detail=f"Error al contactar el servicio de autenticación: {exc}")
    except httpx.HTTPStatusError as exc:
        # El servicio de login devolvió un error 4xx o 5xx (distinto de 401)
        raise HTTPException(status_code=502, detail=f"Error del servicio de autenticación: {exc.response.text}")