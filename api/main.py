from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector

# ===========================
# Configuración de FastAPI
# ===========================
app = FastAPI(
    title="API de prueba superprueba",
    description="CRUD con MySQL para probar CI/CD.",
    version="2.0.0"
)

# ===========================
# Conexión a MySQL
# ===========================
db_config = {
    "host": "mysql",           # nombre del contenedor en docker-compose
    "user": "appUser",
    "password": "AppUser123",
    "database": "catalogo"
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
    new_item = cursor.fetchone()
    return new_item

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
