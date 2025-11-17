# schemas/rubro.py
from pydantic import BaseModel
from typing import Optional

class RubroBase(BaseModel):
    nombre: str
    activo: Optional[bool] = None

class RubroCreate(RubroBase):
    pass

class RubroUpdate(BaseModel):
    nombre: Optional[str] = None

class RubroOut(RubroBase):
    id: int