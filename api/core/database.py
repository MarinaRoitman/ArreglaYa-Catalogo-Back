from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import mysql.connector
import contextlib

load_dotenv()

# ===========================
# Configuración DB desde env
# ===========================


db_config = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "catalogo-dev"),
}

@contextlib.contextmanager
def get_connection():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor,conn
    finally:
        cursor.close()
        conn.close()


# URL de conexión a MySQL (para usar sqlalchemy (no me funcionó))
"""
#obtenerlos desde el .env
DATABASE_URL = (
    f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('MYSQL_DATABASE')}"
)
#DATABASE_URL = "mysql+pymysql://root:password@localhost:3306/arreglaya"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para usar en los endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
