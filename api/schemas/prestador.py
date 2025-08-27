from pydantic import BaseModel
from typing import Optional

class PrestadorBase(BaseModel):
    nombre: str
    email: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    estado: Optional[str] = "Pendiente"
    calificacion: Optional[float] = 0.0
    zona: Optional[str] = None
    precio_por_hora: Optional[float] = None
    especialidad: Optional[str] = None

class PrestadorCreate(PrestadorBase):
    pass

class PrestadorUpdate(BaseModel):
    nombre: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    estado: Optional[str]
    calificacion: Optional[float]
    zona: Optional[str]
    precio_por_hora: Optional[float]
    especialidad: Optional[str]

class PrestadorOut(PrestadorBase):
    id: int
