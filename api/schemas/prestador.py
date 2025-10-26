# schemas/prestador.py
from pydantic import BaseModel
from typing import Optional
from .usuario import UsuarioBase, UsuarioOut

class PrestadorBase(UsuarioBase):
    email: Optional[str] = None
    telefono: Optional[str] = None
    foto: Optional[str] = None
    estado: Optional[str] = None
    ciudad: Optional[str] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    piso: Optional[str] = None
    departamento: Optional[str] = None

class PrestadorCreate(PrestadorBase):
    password: Optional[str] = None
    id_prestador: Optional[int] = None

class PrestadorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None
    contrasena: Optional[str] = None
    dni: Optional[str] = None
    habilidades: Optional[list] = None
    zonas: Optional[list] = None
    foto: Optional[str] = None
    estado: Optional[str] = None
    ciudad: Optional[str] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    piso: Optional[str] = None
    departamento: Optional[str] = None

class PrestadorOut(BaseModel):
    id: Optional[int] = None
    nombre: str
    apellido: str
    email: str
    telefono: Optional[str] = None
    dni: Optional[str] = None
    activo: bool
    habilidades: Optional[list] = None
    zonas: Optional[list] = None
    foto: Optional[str] = None
    estado: Optional[str] = None
    ciudad: Optional[str] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    piso: Optional[str] = None
    departamento: Optional[str] = None
    id_prestador: Optional[int] = None