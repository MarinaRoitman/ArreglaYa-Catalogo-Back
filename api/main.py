from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId

# ===========================
# Configuración de FastAPI
# ===========================
app = FastAPI(
    title="API de prueba",
    description="Estas rutas solo son de prueba para comprobar el funcionamiento correcto de la base de datos y el CI/CD del repo backend de Github.",
    version="1.0.0"
)

# ===========================
# Conexión a MongoDB
# ===========================
MONGO_URI = "mongodb://appUser:m9s018394@mongo:27017/catalogo?authSource=catalogo"
client = MongoClient(MONGO_URI)
db = client["catalogo"]
collection = db["items"]

# ===========================
# Modelos
# ===========================
class Item(BaseModel):
    name: str
    description: str | None = None

class ItemInDB(Item):
    id: str

# ===========================
# Helpers
# ===========================
def item_serializer(item) -> dict:
    """Convierte ObjectId a string para JSON"""
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "description": item.get("description")
    }

# ===========================
# Rutas CRUD
# ===========================

# Crear
@app.post("/items", response_model=ItemInDB)
def create_item(item: Item):
    result = collection.insert_one(item.dict())
    new_item = collection.find_one({"_id": result.inserted_id})
    return item_serializer(new_item)

# Leer todos
@app.get("/items", response_model=list[ItemInDB])
def list_items():
    items = [item_serializer(doc) for doc in collection.find()]
    return items

# Leer uno
@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: str):
    item = collection.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_serializer(item)

# Actualizar
@app.put("/items/{item_id}", response_model=ItemInDB)
def update_item(item_id: str, item: Item):
    result = collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": item.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    updated_item = collection.find_one({"_id": ObjectId(item_id)})
    return item_serializer(updated_item)

# Eliminar
@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    result = collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}
