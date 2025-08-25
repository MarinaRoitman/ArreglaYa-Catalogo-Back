import os
import mysql.connector
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ===========================
# Configuración de FastAPI
# ===========================
app = FastAPI(
    title="API de prueba superprueba",
    description="Estas rutas solo son de prueba para comprobar el funcionamiento correcto de la base de datos y el CI/CD del repo backend de Github.",
    version="1.0.0"
)

# ===========================
# Configuración DB desde env
# ===========================
db_config = {
    "host": os.getenv("DB_HOST", "mysql"),  # en docker-compose el servicio se llama "mysql"
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "appUser"),
    "password": os.getenv("MYSQL_PASSWORD", "AppUser123"),
    "database": os.getenv("MYSQL_DATABASE", "catalogo"),
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# ===========================
# Modelos
# ===========================
class Item(BaseModel):
    name: str
    description: str | None = None

class ItemInDB(Item):
    id: int

# ===========================
# Rutas CRUD
# ===========================
@app.post("/items", response_model=ItemInDB)
def create_item(item: Item):
    cursor.execute(
        "INSERT INTO items (name, description) VALUES (%s, %s)",
        (item.name, item.description)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM items WHERE id = %s", (new_id,))
    return cursor.fetchone()

@app.get("/items", response_model=list[ItemInDB])
def list_items():
    cursor.execute("SELECT * FROM items")
    return cursor.fetchall()

@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: int):
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemInDB)
def update_item(item_id: int, item: Item):
    cursor.execute(
        "UPDATE items SET name=%s, description=%s WHERE id=%s",
        (item.name, item.description, item_id)
    )
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    return cursor.fetchone()

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}
