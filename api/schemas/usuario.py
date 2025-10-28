# schemas/usuario.py
from pydantic import BaseModel
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    foto: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    telefono: Optional[str] = None
    id_usuario: Optional[int] = None
    estado_pri: Optional[str] = None
    ciudad_pri: Optional[str] = None
    calle_pri: Optional[str] = None
    numero_pri: Optional[str] = None
    piso_pri: Optional[str] = None
    departamento_pri: Optional[str] = None
    estado_sec: Optional[str] = None
    ciudad_sec: Optional[str] = None
    calle_sec: Optional[str] = None
    numero_sec: Optional[str] = None
    piso_sec: Optional[str] = None
    departamento_sec: Optional[str] = None
    id_usuario: Optional[int] = None

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    estado_pri: Optional[str] = None
    ciudad_pri: Optional[str] = None
    calle_pri: Optional[str] = None
    numero_pri: Optional[str] = None
    piso_pri: Optional[str] = None
    departamento_pri: Optional[str] = None
    estado_sec: Optional[str] = None
    ciudad_sec: Optional[str] = None
    calle_sec: Optional[str] = None
    numero_sec: Optional[str] = None
    piso_sec: Optional[str] = None
    departamento_sec: Optional[str] = None
    telefono: Optional[str] = None
    id_usuario: Optional[int] = None
    foto: Optional[str] = None

class UsuarioOut(UsuarioBase):
    id: int
    telefono: Optional[str] = None
    activo: bool
    estado_pri: Optional[str] = None
    ciudad_pri: Optional[str] = None
    calle_pri: Optional[str] = None
    numero_pri: Optional[str] = None
    piso_pri: Optional[str] = None
    departamento_pri: Optional[str] = None
    estado_sec: Optional[str] = None
    ciudad_sec: Optional[str] = None
    calle_sec: Optional[str] = None
    numero_sec: Optional[str] = None
    piso_sec: Optional[str] = None
    departamento_sec: Optional[str] = None
    id_usuario: Optional[int] = None
