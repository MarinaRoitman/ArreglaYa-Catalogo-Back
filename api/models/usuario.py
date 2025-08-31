# models/usuario.py
class Usuario:
    def __init__(self, id, nombre, apellido, direccion, email):
        self.id = id
        self.nombre = nombre
        self.apellido = apellido
        self.direccion = direccion
        self.email = email


"""
# Si usas SQLAlchemy (comentado para referencia)
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    direccion = Column(String(255), nullable=True)
"""