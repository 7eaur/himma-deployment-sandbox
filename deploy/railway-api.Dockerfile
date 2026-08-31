# Railway sandbox deployment image
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

WORKDIR /app/services/api

# Railway may override CMD with a command containing $PORT without shell expansion.
# Keep a shell ENTRYPOINT so both Railway overrides and the default CMD expand env vars.
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
