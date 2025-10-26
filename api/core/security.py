from datetime import datetime, timedelta
from jose import jwt, JWTError
import hmac
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Security, Header
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
import os

INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

bearer_scheme = HTTPBearer(auto_error=True)


# Deprecated: usar alguno de los require_..._role
def get_current_user_swagger(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return {"id": user_id, "role": role}
    except JWTError:
        raise credentials_exception

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Deprecated
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
        return {"id": user_id, "role": role}
    except JWTError:
        raise credentials_exception

def require_prestador_role(current_user: dict = Depends(get_current_user_swagger)):
    if current_user.get("role") != "prestador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )
    return current_user

def require_admin_role(current_user: dict = Depends(get_current_user_swagger)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso permitido solo para administradores"
        )
    return current_user

def get_current_user_optional(authorization: str = Header(None)):
    """Versión opcional del decode, no falla si no hay token."""
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": payload.get("sub"), "role": payload.get("role")}
    except Exception:
        return None

def require_internal_or_admin(
    x_internal_token: str = Header(None),
    authorization: str = Header(None)
):
    # 1️⃣ Si viene el token interno válido → OK
    if x_internal_token and x_internal_token == INTERNAL_API_TOKEN:
        return {"role": "internal"}

    # 2️⃣ Caso contrario, tratamos de validar el JWT si existe
    user = get_current_user_optional(authorization)
    if user and user.get("role") == "admin":
        return user

    # 3️⃣ Si no pasó ninguno, rechazamos
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Acceso no autorizado (se requiere rol admin o token interno.){x_internal_token}|{INTERNAL_API_TOKEN}"
    )

def require_admin_or_prestador_role(current_user: dict = Depends(get_current_user_swagger)):
    if current_user.get("role") not in ["admin", "prestador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso permitido solo para administradores o prestadores"
        )
    return current_user

def require_internal_admin_or_prestador(
    x_internal_token: str = Header(None),
    authorization: str = Header(None)
):
    if x_internal_token and x_internal_token == INTERNAL_API_TOKEN:
        return {"role": "internal"}

    user = get_current_user_optional(authorization)
    
    if user and user.get("role") in ["admin", "prestador"]:
        return user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acceso permitido solo para administradores, prestadores o con token interno"
    )