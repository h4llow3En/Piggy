# Stage 1: Build & Requirements
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim AS runtime

LABEL authors="Felix Doering <development@felixdoering.com>"

# Create a non-root user
RUN groupadd -g 10001 piggy && \
    useradd -u 10001 -g piggy -m -s /bin/bash piggy

WORKDIR /app

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY requirements.txt alembic.ini ./
COPY alembic /app/alembic
COPY piggy /app/piggy
COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && \
    chown -R piggy:piggy /app /entrypoint.sh

USER piggy

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD nc -z localhost 8000 || exit 1

ENTRYPOINT ["/entrypoint.sh"]