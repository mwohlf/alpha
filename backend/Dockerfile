# ==========================================
# Stage 1: The Builder, 
# we don't rely on the host we build (again) on the same arch as the runner 
# ==========================================
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    build-essential \
    gcc \
    python3-dev \
    libcairo2-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    libgirepository-2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
# Ensure subsequent python/pip commands use the venv
ENV PATH="/opt/venv/bin:$PATH"

COPY backend/requirements.txt .

# Use BuildKit cache to speed up pip installs
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# Stage 2: The Runner (Final Production Image)
# ==========================================
FROM python:3.14-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/backend"

WORKDIR /app

# Install RUNTIME dependencies (See notes below)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libglib2.0-0 \
    libjpeg62-turbo \
    gir1.2-glib-2.0 \
    && rm -rf /var/lib/apt/lists/*

# Create user FIRST
RUN adduser --disabled-password --gecos "" appuser

# TODO: copy this from the host, no need to re-install in the builder
# Copy the venv from builder (avoids pip install in runner)
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Copy code WITH correct ownership in one step
COPY --chown=appuser:appuser backend/ /app/backend/
COPY --chown=appuser:appuser frontend/dist/ /app/frontend/dist/

USER appuser

EXPOSE 8000

CMD ["/opt/venv/bin/python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]