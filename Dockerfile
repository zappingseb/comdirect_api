FROM python:3.6-slim

WORKDIR /app


RUN apt-get update && \
  apt-get install -y \
  git \
  gcc \
  python3-dev \
  zlib1g-dev \
  libjpeg-dev \
  build-essential && \
  rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy directories maintaining structure
COPY base/ ./base/
COPY comdirect/ ./comdirect/
COPY paypal/ ./paypal/
COPY hanseatic/ ./hanseatic/
COPY csv_adapter/ ./csv_adapter/
COPY server/ ./server/

ENV PYTHONPATH=/app

EXPOSE 80

CMD ["python", "server/server.py"]