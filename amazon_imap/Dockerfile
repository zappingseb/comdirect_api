FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        libssl-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir gunicorn==22.0.0

COPY main.py .
COPY services/ ./services/

EXPOSE 5000

CMD ["gunicorn", "--workers", "1", "--timeout", "60", "--bind", "0.0.0.0:5000", "main:app"]
