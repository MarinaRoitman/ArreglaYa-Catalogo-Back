# schemas/usuario.py
from pydantic import BaseModel
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    direccion: str
    dni: str
    id_usuario: Optional[int] = None
    foto: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    telefono: Optional[str] = None
    id_usuario: Optional[int] = None

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    direccion: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    id_usuario: Optional[int] = None
    foto: Optional[str] = None

class UsuarioOut(UsuarioBase):
    id: int
    telefono: Optional[str] = None
    activo: bool
    id_usuario: Optional[int] = None
    foto: Optional[str] = None
