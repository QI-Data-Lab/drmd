FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional; add as needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY webapp/requirements.txt /app/webapp/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/webapp/requirements.txt

# Copy repo
COPY . /app

# Env for resource paths (app also sets these automatically)
ENV DRMD_XSD_PATH=/app/v0.3.0/xsd/drmd.xsd \
    DRMD_XSL_PATH=/app/v0.3.0/xsl/drmd.xsl \
    QUDT_TTL_PATH=/app/imports/qudt.ttl

EXPOSE 8501

CMD ["streamlit", "run", "webapp/app.py", "--server.headless=true", "--server.port=8501"]
