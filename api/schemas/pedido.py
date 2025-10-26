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
    estado: EstadoPedido = EstadoPedido.pendiente
    tarifa: Optional[float] = None
    descripcion: Optional[str] = None
    id_usuario: Optional[int] = None
    id_prestador: Optional[int] = None
    fecha: Optional[datetime] = None
    id_habilidad: Optional[int] = None
    id_pedido: Optional[int] = None
    es_critico: Optional[bool] = False
    id_zona: Optional[int] = None
    

class PedidoCreate(PedidoBase):
    pass

class PedidoUpdate(BaseModel):
    estado: Optional[EstadoPedido] = None
    tarifa: Optional[float] = None
    id_prestador: Optional[int] = None
    fecha: Optional[datetime] = None
    id_habilidad: Optional[int] = None
    id_pedido: Optional[int] = None
    es_critico: Optional[bool] = None
    id_zona: Optional[int] = None
    
class PedidoOut(PedidoBase):
    id: Optional[int] = None
    fecha_creacion: datetime
    fecha_ultima_actualizacion: datetime
    fecha: Optional[datetime] = None
    id_pedido: Optional[int] = None
    es_critico: bool
    
    