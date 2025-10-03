from fastapi import FastAPI, Request, Header, HTTPException
from starlette.responses import JSONResponse
import os, json, logging, pymysql
from dotenv import load_dotenv

# ===========================
# Cargar variables desde .env
# ===========================
load_dotenv()

# Config logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger("webhook")

app = FastAPI()

# ===========================
# Configuración DB desde env
# ===========================
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER")
DB_PASS = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE", "catalogo")

# Validación de env obligatorias
REQUIRED = ["DB_HOST", "DB_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    raise SystemExit(f"Faltan variables de entorno: {', '.join(missing)}")

def db():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=DB_NAME, cursorclass=pymysql.cursors.DictCursor, autocommit=True
    )

# ===========================
# Healthcheck endpoint
# ===========================
@app.get("/health")
async def health():
    return {"ok": True}

# ===========================
# Webhook endpoint
# ===========================
@app.post("/webhook")
async def webhook(
    request: Request,
    x_signature: str | None = Header(default=None),
    x_subscription_id: str | None = Header(default=None),
):
    raw = await request.body()
    log.info("📩 New request received")

    try:
        body = json.loads(raw.decode("utf-8"))
    except Exception:
        log.warning("❌ Invalid JSON received")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Datos del evento publish
    msg_id       = body.get("messageId")
    source       = body.get("source")
    destination  = body.get("destination", {})
    channel      = destination.get("channel")
    event_name   = destination.get("eventName")
    subscription = x_subscription_id or body.get("subscriptionId")

    if not msg_id:
        log.warning("⚠️ Request missing messageId, rejecting")
        raise HTTPException(status_code=400, detail="Missing messageId")

    log.info(
        f"✅ Request parsed: messageId={msg_id}, subscriptionId={subscription}, "
        f"channel={channel}, eventName={event_name}"
    )

    # Persistencia idempotente
    try:
        conn = db()
        with conn.cursor() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS inbound_events (
                  id BIGINT AUTO_INCREMENT PRIMARY KEY,
                  message_id VARCHAR(128) NOT NULL UNIQUE,
                  subscription_id VARCHAR(128) NULL,
                  source VARCHAR(100),
                  channel VARCHAR(200),
                  event_name VARCHAR(100),
                  payload JSON NOT NULL,
                  received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  processed_at TIMESTAMP NULL,
                  status ENUM('pending','processing','done','error') DEFAULT 'pending',
                  error_text TEXT NULL
                )
            """)
            c.execute("""
                INSERT INTO inbound_events (message_id, subscription_id, source, channel, event_name, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE payload = VALUES(payload)
            """, (msg_id, subscription, source, channel, event_name, json.dumps(body)))
        log.info(f"📝 Event persisted in DB: messageId={msg_id}")
    except Exception as e:
        log.exception(f"💥 DB insert failed for messageId={msg_id}: {e}")
        raise HTTPException(status_code=500, detail="Persistence failed")

    # Responder rápido 2xx
    log.info(f"✅ Responding 200 OK for messageId={msg_id}")
    return JSONResponse({"received": True, "messageId": msg_id})
