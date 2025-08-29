from .usuario import Usuario
class Prestador(Usuario):
    def __init__(self, id, nombre, apellido, direccion, email, telefono, id_zona):
        # Llamamos al constructor de la clase padre (Usuario)
        super().__init__(id, nombre, apellido, direccion)
        # Agregamos los atributos específicos de Prestador
        self.email = email
        self.telefono = telefono
        self.id_zona = id_zona


"""
# Si usas SQLAlchemy (comentado para referencia)
class Prestador(Base):
    __tablename__ = "prestadores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    telefono = Column(String(20), nullable=True)
    direccion = Column(String(255), nullable=True)
    id_zona = Column(Integer, nullable=True)
"""