FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build deps and project dependencies first (layer caching)
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY src ./src
COPY scripts ./scripts

EXPOSE 8000 8100

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
