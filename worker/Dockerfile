FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ⬇️ Copiá todo el worker (ajusta la ruta al contexto real de build)
# Si tu Docker build se ejecuta desde api/worker/, con esto basta:
COPY . /app/

# Si preferís ser explícita:
# COPY worker.py process.py config.py core_ack.py /app/
# COPY handlers/ /app/handlers/

CMD ["python","-u","/app/worker.py"]
