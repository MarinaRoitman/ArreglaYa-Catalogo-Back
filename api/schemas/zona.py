from pydantic import BaseModel
from typing import Optional

class ZonaBase(BaseModel):
    nombre: str

class ZonaCreate(ZonaBase):
    pass

class ZonaUpdate(BaseModel):
    nombre: Optional[str] = None

class ZonaOut(ZonaBase):
    id: int
    nombre: str