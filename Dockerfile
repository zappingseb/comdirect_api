FROM debian:bullseye
WORKDIR /app

# Install Python packages from apt
RUN  apt-get update && apt-get install -y python3.10 python3-pip python3-yaml python3-numpy && rm -rf /var/lib/apt/lists/*
RUN  apt-get update && apt-get install -y python3-pandas python3-pil python3-fitz \
  && rm -rf /var/lib/apt/lists/*



# Install pip packages
COPY requirements.txt /tmp/requirements.orig
RUN apt-get update && apt-get install -y git
# Set Python path and verify installations
ENV PYTHONPATH=/usr/lib/python3/dist-packages:/app

RUN pip3 install wheel importlib-metadata && \
  grep -v "pandas\|Pillow\|numpy\|pymupdf" /tmp/requirements.orig > requirements.txt && \
  pip3 install --target=/usr/lib/python3/dist-packages -r requirements.txt


# Copy application files
COPY base/ ./base/
COPY comdirect/ ./comdirect/
COPY paypal/ ./paypal/
COPY hanseatic/ ./hanseatic/
COPY csv_adapter/ ./csv_adapter/
COPY server/ ./server/

ENV PYTHONPATH=/usr/lib/python3/site-packages:/usr/lib/python3/dist-packages:/app
# Verify installations
RUN python3 -c "import numpy; import PIL; import pandas; import fitz; print(f'fitz version: {fitz.__file__}'); print(f'PIL version: {PIL.__version__}'); print(f'pandas version: {pandas.__version__}')"

EXPOSE 80
CMD ["python3", "server/server.py"]