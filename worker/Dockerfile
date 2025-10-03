FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copia el script del worker
COPY worker.py /app/worker.py

# sin puertos; no es HTTP
CMD ["python","-u","/app/worker.py"]
