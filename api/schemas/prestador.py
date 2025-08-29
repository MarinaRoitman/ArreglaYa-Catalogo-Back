# schemas/prestador.py
from pydantic import BaseModel
from typing import Optional
from .usuario import UsuarioBase, UsuarioOut

class PrestadorBase(UsuarioBase):
    email: str
    telefono: Optional[str] = None
    id_zona: Optional[int] = None

class PrestadorCreate(PrestadorBase):
    pass

class PrestadorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    direccion: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    id_zona: Optional[int] = None

class PrestadorOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    direccion: Optional[str] = None
    email: str
    telefono: Optional[str] = None
    id_zona: Optional[int] = None
