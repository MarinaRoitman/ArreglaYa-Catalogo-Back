# schemas/rubro.py
from pydantic import BaseModel
from typing import Optional

class RubroBase(BaseModel):
    nombre: str

class RubroCreate(RubroBase):
    pass

class RubroUpdate(BaseModel):
    nombre: Optional[str] = None

class RubroOut(RubroBase):
    id: int