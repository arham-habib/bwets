FROM python:3.12-slim

# 1) system deps
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# 2) python deps
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) source
COPY app/ app/
COPY scripts/ scripts/
COPY .env .env

EXPOSE 8080
CMD ["bash", "-c", "gunicorn -k uvicorn.workers.UvicornWorker app.ui:create_app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 --log-level info"]
