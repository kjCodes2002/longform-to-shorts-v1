# ---- Base image ----
FROM python:3.12-slim

# ---- System dependencies ----
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# ---- Working directory ----
WORKDIR /app

# ---- Python dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code ----
COPY scripts/ scripts/
COPY server/ server/

# ---- Create directories for runtime files ----
RUN mkdir -p audio clipped .cache

# ---- Default port (Render injects $PORT) ----
ENV PORT=8000

# ---- Start the server ----
CMD uvicorn server.app:app --host 0.0.0.0 --port $PORT
