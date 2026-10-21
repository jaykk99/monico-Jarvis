# --- monico-Jarvis production image -----------------------------------------
# Keyless app: no build secrets, no network calls at runtime. Health-checked
# on /ready (skills loaded + data dir writable) so orchestrators only route
# traffic to a fully booted instance.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Non-root user first so copied files can be owned by it.
RUN groupadd -r jarvis && useradd -r -g jarvis -d /app jarvis \
    && mkdir -p /app/data && chown -R jarvis:jarvis /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=jarvis:jarvis main.py agent.py config.py .env.example ./
COPY --chown=jarvis:jarvis skills/ ./skills/
COPY --chown=jarvis:jarvis static/ ./static/
COPY --chown=jarvis:jarvis api/ ./api/

USER jarvis

# Data persists here; mount a volume in production so notes/todos survive
# container restarts.
VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=4).status == 200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
