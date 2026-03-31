FROM python:3.13-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir pdm && \
    pdm install -G minio -G redis -G observability

EXPOSE 8000
CMD ["pdm", "run", "uvicorn", "promptdb.api:app", "--host", "0.0.0.0", "--port", "8000"]
