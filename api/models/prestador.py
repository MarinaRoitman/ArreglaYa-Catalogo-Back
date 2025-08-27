class Prestador:
    def __init__(self, id, nombre, email, direccion, telefono, estado, calificacion, zona, precio_por_hora, especialidad):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.direccion = direccion
        self.telefono = telefono
        self.estado = estado
        self.calificacion = calificacion
        self.zona = zona
        self.precio_por_hora = precio_por_hora
        self.especialidad = especialidad


"""
class Prestador(Base):
    __tablename__ = "prestadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    rubro = Column(String(50), nullable=False)
    zona = Column(String(50), nullable=True)
"""