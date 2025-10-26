from pydantic import BaseModel
from typing import Optional

class AdminBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    id_admin: Optional[int] = None
    foto: Optional[str] = None

class AdminCreate(AdminBase):
    password:  Optional[str] = None
    id_admin: Optional[int] = None

class AdminUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    id_admin: Optional[int] = None
    foto: Optional[str] = None

class AdminOut(AdminBase):
    id: int
    activo: bool
    id_admin: Optional[int] = None
    foto: Optional[str] = None