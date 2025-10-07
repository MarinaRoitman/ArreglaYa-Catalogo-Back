# schemas/prestador.py
from pydantic import BaseModel
from typing import Optional
from .usuario import UsuarioBase, UsuarioOut

class PrestadorBase(UsuarioBase):
    email: Optional[str] = None
    telefono: Optional[str] = None

class PrestadorCreate(PrestadorBase):
    password: str

class PrestadorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    direccion: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None
    contrasena: Optional[str] = None
    dni: Optional[str] = None
    habilidades: Optional[list] = None
    zonas: Optional[list] = None

class PrestadorOut(BaseModel):
    id: int
    nombre: str
    apellido: str
    direccion: Optional[str] = None
    email: str
    telefono: Optional[str] = None
    dni: Optional[str] = None
    activo: bool
    habilidades: Optional[list] = None
    zonas: Optional[list] = None
