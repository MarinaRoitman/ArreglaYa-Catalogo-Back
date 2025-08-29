# schemas/pedido.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class EstadoPedido(str, Enum):
    pendiente = "pendiente"
    aprobado_por_prestador = "aprobado_por_prestador"
    aprobado_por_usuario = "aprobado_por_usuario"
    finalizado = "finalizado"
    cancelado = "cancelado"

class PedidoBase(BaseModel):
    estado: EstadoPedido
    tarifa: Optional[float] = None
    id_prestador: int
    id_usuario: int

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(BaseModel):
    estado: Optional[EstadoPedido] = None
    tarifa: Optional[float] = None

class PedidoOut(PedidoBase):
    id: int
    fecha_creacion: datetime
    fecha_ultima_actualizacion: datetime