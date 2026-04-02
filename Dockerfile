FROM python:3.11-slim

WORKDIR /app

# FAISS runtime dependency
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY scripts/ scripts/
COPY config/ config/

# Set Python path for imports
ENV PYTHONPATH=/app/src

# Cloud Run sets PORT env var
CMD ["python", "scripts/start_server.py"]
