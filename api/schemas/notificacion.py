# schemas/notificacion.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificacionBase(BaseModel):
    titulo: str
    mensaje: Optional[str] = None
    visible: bool = True
    id_pedido: int

class NotificacionCreate(NotificacionBase):
    pass

class NotificacionUpdate(BaseModel):
    titulo: Optional[str] = None
    mensaje: Optional[str] = None
    visible: Optional[bool] = None

class NotificacionOut(NotificacionBase):
    id: int
    fecha: datetime
    id_pedido: Optional[int] = None