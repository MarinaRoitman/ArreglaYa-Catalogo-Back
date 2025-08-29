# models/notificacion.py
class Notificacion:
    def __init__(self, id, titulo, mensaje, fecha, visible, id_pedido):
        self.id = id
        self.titulo = titulo
        self.mensaje = mensaje
        self.fecha = fecha
        self.visible = visible
        self.id_pedido = id_pedido