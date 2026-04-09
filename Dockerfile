# Stage 1: Build frontend
FROM node:22-slim AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser -m appuser

COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir ".[web]"

# Copy built frontend into package
COPY --from=frontend /app/web/dist/ src/alertforge/web_dist/

# Copy model artifacts if present
COPY data/models/ data/models/ 2>/dev/null || true

USER appuser
EXPOSE 8000

CMD ["uvicorn", "alertforge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
