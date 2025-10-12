# models/usuario.py
class Usuario:
    def __init__(self, id, nombre, apellido, direccion, dni, telefono=None, activo=True, id_usuario=None, foto=None):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.direccion = direccion
        self.dni = dni
        self.telefono = telefono
        self.activo = activo
        self.id_usuario = id_usuario
        self.foto = foto