# models/usuario.py
class Usuario:
    def __init__(self, id, nombre, apellido, dni, telefono=None, activo=True, id_usuario=None, foto=None,
                 estado_pri=None, ciudad_pri=None, calle_pri=None, numero_pri=None,
                 piso_pri=None, departamento_pri=None, estado_sec=None, ciudad_sec=None, calle_sec=None,
                 numero_sec=None, piso_sec=None, departamento_sec=None):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.telefono = telefono
        self.activo = activo
        self.id_usuario = id_usuario
        self.foto = foto
        self.estado_pri = estado_pri
        self.ciudad_pri = ciudad_pri
        self.calle_pri = calle_pri
        self.numero_pri = numero_pri
        self.piso_pri = piso_pri
        self.departamento_pri = departamento_pri
        self.estado_sec = estado_sec
        self.ciudad_sec = ciudad_sec
        self.calle_sec = calle_sec
        self.numero_sec = numero_sec
        self.piso_sec = piso_sec
        self.departamento_sec = departamento_sec