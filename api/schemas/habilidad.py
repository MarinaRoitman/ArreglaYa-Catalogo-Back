# schemas/habilidad.py
from pydantic import BaseModel
from typing import Optional

class HabilidadBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_rubro: int
    activo: Optional[bool] = True

class HabilidadCreate(HabilidadBase):
    pass

class HabilidadUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    id_rubro: Optional[int] = None

class HabilidadOut(HabilidadBase):
    id: int
    activo: Optional[bool] = None