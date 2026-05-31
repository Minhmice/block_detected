FROM python:3.11-slim-bookworm AS backend

WORKDIR /app
COPY backend/requirements-dev.txt backend/requirements-dev.txt
RUN pip install --no-cache-dir -r backend/requirements-dev.txt

COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
COPY images ./images
COPY backend ./backend
RUN pip install --no-cache-dir -e .

ENV MOCK_CAMERA=true
ENV DETECTION_MODE=mock
ENV CORS_ORIGINS=http://localhost:3000
ENV PYTHONPATH=/app/backend

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
