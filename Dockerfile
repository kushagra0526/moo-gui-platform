# ── Stage 1: build dependencies ────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build tools needed by some wheels (numpy, scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ─────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create writable runtime directories (experiments, exports, database)
RUN mkdir -p database experiments exports \
    && chmod -R 777 database experiments exports

# Expose the port Dash listens on
EXPOSE 8080

# Run as non-root for security
RUN useradd -m appuser
USER appuser

# Entry point — one worker: the running optimization lives in that process's memory
CMD ["gunicorn", "--workers=1", "--threads=4", "--timeout=120", "--bind=0.0.0.0:8080", "main:server"]
