FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CUADERNOPRO_DATA_DIR=/app/runtime \
    CUADERNOPRO_DB_PATH=/app/runtime/cuadernopro.db \
    CUADERNOPRO_BACKUPS_DIR=/app/runtime/backups \
    CUADERNOPRO_EXPORTS_DIR=/app/runtime/exports \
    CUADERNOPRO_DOCUMENTOS_DIR=/app/runtime/documentos

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

RUN mkdir -p \
    /app/runtime/backups \
    /app/runtime/exports \
    /app/runtime/documentos

VOLUME ["/app/runtime"]

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
