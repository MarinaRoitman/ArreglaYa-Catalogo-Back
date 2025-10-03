FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el archivo como /app/webhook.py y apuntamos a "webhook:app"
COPY webhook.py /app/webhook.py

EXPOSE 8081

# Importante: CMD en una sola línea JSON
CMD ["gunicorn","webhook:app","-k","uvicorn.workers.UvicornWorker","-w","2","-b","0.0.0.0:8081","--timeout","20","--keep-alive","5"]
