# schemas/usuario.py
from pydantic import BaseModel
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    telefono: str
    username: str
    password: str
    direccion: str

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    direccion: Optional[str] = None

class UsuarioOut(UsuarioBase):
    id: int