from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from api.core.database import get_connection
from api.routes import prestadores, auth

# ===========================
# Configuración de FastAPI
# ===========================
app = FastAPI(
    title="API de prueba superprueba",
    description="Estas rutas solo son de prueba para comprobar el funcionamiento correcto de la base de datos y el CI/CD del repo backend de Github.",
    version="1.0.0"
)

app.include_router(prestadores.router)
app.include_router(auth.router)
# ===========================
# Prometheus Metrics
# ===========================
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, endpoint="/metrics", include_in_schema=False, should_gzip=True)

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
"""
@app.get("/prestadores", response_model=list[Prestador])
def list_prestadores():
    try:
        cursor.execute("SELECT * FROM prestadores")
        return cursor.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@app.post("/items", response_model=ItemInDB)
def create_item(item: Item):
    conn = get_connection()
    cursor = conn.cursor()
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    return cursor.fetchall()

@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=ItemInDB)
def update_item(item_id: int, item: Item):
    conn = get_connection()
    cursor = conn.cursor()
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}
"""