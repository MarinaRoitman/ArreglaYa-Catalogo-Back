# models/calificacion.py
class Calificacion:
    def __init__(self, id, estrellas, descripcion, id_prestador, id_usuario):
        self.id = id
        self.estrellas = estrellas
        self.descripcion = descripcion
        self.id_prestador = id_prestador
        self.id_usuario = id_usuario