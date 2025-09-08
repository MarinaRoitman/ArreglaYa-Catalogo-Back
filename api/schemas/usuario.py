# schemas/usuario.py
from pydantic import BaseModel
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    direccion: str
    dni: str

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    direccion: Optional[str] = None
    dni: Optional[str] = None


class UsuarioOut(UsuarioBase):
    id: int