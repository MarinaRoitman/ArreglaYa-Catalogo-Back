# schemas/calificacion.py
from pydantic import BaseModel
from typing import Optional

class CalificacionBase(BaseModel):
    estrellas: float
    descripcion: Optional[str] = None
    id_prestador: int
    id_usuario: int

class CalificacionCreate(CalificacionBase):
    pass

class CalificacionUpdate(BaseModel):
    estrellas: Optional[float] = None
    descripcion: Optional[str] = None

class CalificacionOut(CalificacionBase):
    id: int