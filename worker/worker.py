# api/worker/worker.py
import os, time, logging, pymysql, uuid
from dotenv import load_dotenv
from process import process_message
import requests

# Cargar .env (busca en el cwd y en la raíz del proyecto)
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "2"))

# ===========================
# Configuración DB desde env
# ===========================
db_config = {
    "host": os.getenv("DB_HOST", "mysql"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE", "catalogo"),
}

# Validación de variables obligatorias
REQUIRED = ["DB_HOST", "DB_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"]
missing = [k for k in REQUIRED if not os.getenv(k)]
if missing:
    raise SystemExit(f"Faltan variables de entorno: {', '.join(missing)}")

def db():
    return pymysql.connect(
        host=db_config["host"], port=db_config["port"],
        user=db_config["user"], password=db_config["password"],
        database=db_config["database"], autocommit=False,
        cursorclass=pymysql.cursors.DictCursor
    )

def ensure_schema(conn):
    with conn.cursor() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS inbound_events (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              message_id VARCHAR(128) NOT NULL UNIQUE,
              subscription_id VARCHAR(128) NULL,
              topic VARCHAR(200),
              event_name VARCHAR(100),
              payload JSON NOT NULL,
              received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              processed_at TIMESTAMP NULL,
              status ENUM('pending','processing','done','error') DEFAULT 'pending',
              error_text TEXT NULL
            )
        """)
    conn.commit()

def claim_one(conn):
    try:
        with conn.cursor() as c:
            c.execute("START TRANSACTION")
            try:
                c.execute("""
                    SELECT id, message_id FROM inbound_events
                    WHERE status='pending'
                    ORDER BY received_at, id
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                """)
            except pymysql.err.ProgrammingError:
                c.execute("""
                    SELECT id, message_id FROM inbound_events
                    WHERE status='pending'
                    ORDER BY received_at, id
                    LIMIT 1
                    FOR UPDATE
                """)
            row = c.fetchone()
            if not row:
                conn.rollback()
                return None
            c.execute("UPDATE inbound_events SET status='processing' WHERE id=%s AND status='pending'", (row["id"],))
            conn.commit()
            logging.info(f"Mensaje detectado: messageId={row['message_id']}")
            return row["message_id"]
    except Exception as e:
        logging.exception(f"Error en claim_one: {e}")
        try: conn.rollback()
        except: pass
        return None

# Esto solo simula el procesamiento real
""" 
def process_message(mid):
    logging.info(f"Procesando mensaje messageId={mid}")
    time.sleep(1)
    logging.info(f"Procesamiento terminado messageId={mid}")"""

def run():
    logging.info(f"Worker iniciado id={WORKER_ID}")
    while True:
        try:
            # 🔁 Nueva conexión en cada ciclo
            conn = db()
            ensure_schema(conn)

            msg_id = claim_one(conn)
            if msg_id:
                process_message(conn, msg_id)
                ack_body = {"messageId": f"{msg_id}"}
                ack_headers = {
                    "Content-Type": "application/json",
                    "X-API-KEY": f"{os.getenv('CORE_API_KEY', 'ch_812ec720cd32409693886474bda08640')}"
                }
                requests.post(f"https://nonprodapi.uade-corehub.com/messages/ack/{msg_id}", headers=ack_headers, json=ack_body)
                logging.info(f"Mensaje ackeado messageId={msg_id}")
            else:
                # 🔄 No hay mensajes nuevos, esperar un poco
                logging.debug("Sin mensajes pendientes...")
                time.sleep(POLL_INTERVAL_SEC)

        except pymysql.err.OperationalError as e:
            logging.error(f"Error de conexión con la base de datos: {e}")
            time.sleep(5)  # Reintentar más tarde

        except Exception as e:
            logging.exception(f"💥 Error inesperado en el loop principal: {e}")
            time.sleep(5)

        finally:
            try:
                conn.close()
            except Exception:
                pass  # Evita crash si conn no estaba abierta

if __name__ == "__main__":
    run()
