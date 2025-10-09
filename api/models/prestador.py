from .usuario import Usuario
class Prestador(Usuario):
    def __init__(self, id, nombre, apellido, direccion, telefono, dni=None, activo=True, foto=None):
        # Llamamos al constructor de la clase padre (Usuario)
        super().__init__(id, nombre, apellido, direccion)
        # Agregamos los atributos específicos de Prestador
        self.telefono = telefono
        self.dni = dni
        self.activo = activo
        self.foto = foto
