from .usuario import Usuario
class Prestador(Usuario):
    def __init__(self, id, nombre, apellido, telefono, dni=None, activo=True, foto=None,
                 estado=None, ciudad=None, calle=None, numero=None, piso=None, departamento=None):
        super().__init__(id, nombre, apellido, dni, telefono, activo, foto)
        self.estado = estado
        self.ciudad = ciudad
        self.calle = calle
        self.numero = numero
        self.piso = piso
        self.departamento = departamento
