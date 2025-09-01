from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from core.database import get_connection
from routes import auth, prestadores, zonas, habilidades, rubros
from fastapi.middleware.cors import CORSMiddleware 

# ===========================
# Configuración de FastAPI
# ===========================
app = FastAPI(
    title="API Desarrollo 2",
    description="Estas rutas solo son de prueba para comprobar el funcionamiento correcto de la base de datos y el CI/CD del repo backend de Github.",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(prestadores.router)
app.include_router(zonas.router)
app.include_router(habilidades.router)
app.include_router(rubros.router)

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

