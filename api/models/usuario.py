# models/usuario.py
class Usuario:
    def __init__(self, id, nombre, apellido, direccion, email):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.direccion = direccion
        self.email = email
