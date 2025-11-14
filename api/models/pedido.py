# models/pedido.py
class Pedido:
    def __init__(self, id, estado, tarifa, fecha_creacion, fecha_ultima_actualizacion, id_prestador, id_usuario, direccion, es_critico=False):
        self.id = id
        self.estado = estado
        self.tarifa = tarifa
        self.fecha_creacion = fecha_creacion
        self.fecha_ultima_actualizacion = fecha_ultima_actualizacion
        self.id_prestador = id_prestador
        self.id_usuario = id_usuario
        self.direccion = direccion
        self.es_critico = es_critico
        