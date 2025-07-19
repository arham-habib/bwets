# ───────── base image ─────────
FROM python:3.11-slim

# install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential && rm -rf /var/lib/apt/lists/*

# ───────── app code ──────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ───────── runtime env ───────
ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    DATABASE_URL=sqlite:////data/bwets.db 
# Fly volume mount point
VOLUME ["/data"]

# ───────── entrypoint ────────s
# 1. refresh csv -> db (non‑destructive)
# 2. migrate users table if needed
# 3. start Flask + FastAPI via python -m app
EXPOSE 8080
CMD ["bash", "-c", "python -m scripts.refresh_entities && python -m scripts.migrate_users && python -m app"]
