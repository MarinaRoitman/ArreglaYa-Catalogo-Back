from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from core.database import get_connection
from routes import auth, prestadores, zonas, habilidades, rubros, pedidos, notificaciones,calificaciones, usuarios, admin
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
app.include_router(pedidos.router)
app.include_router(notificaciones.router)
app.include_router(calificaciones.router)
app.include_router(usuarios.router)
app.include_router(admin.router)

#CORS

FRONT_PROD = "https://desarrollo2-catalogos.online"
LOCAL_3000 = "http://localhost:3000" 

ALLOWED_ORIGINS = [FRONT_PROD, LOCAL_3000]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

