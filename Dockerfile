# One same-origin service for a free Render web instance; external PostgreSQL.
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build
COPY frontend/package*.json frontend/.npmrc ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1 API_INTERNAL_URL=http://127.0.0.1:8000
RUN npm run build

FROM python:3.12-slim-bookworm AS python-runtime
FROM node:22-bookworm-slim AS runtime
COPY --from=python-runtime /usr/local/ /usr/local/
WORKDIR /app
COPY backend/requirements.lock.txt ./backend/requirements.lock.txt
RUN pip install --no-cache-dir -r backend/requirements.lock.txt && useradd --create-home resolvedesk && mkdir -p /app/data && chown resolvedesk:resolvedesk /app/data
COPY --chown=resolvedesk:resolvedesk backend/app ./backend/app
COPY --chown=resolvedesk:resolvedesk scripts/serve.py ./scripts/serve.py
COPY --from=frontend-build --chown=resolvedesk:resolvedesk /build/.next/standalone ./frontend
COPY --from=frontend-build --chown=resolvedesk:resolvedesk /build/.next/static ./frontend/.next/static
USER resolvedesk
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NEXT_TELEMETRY_DISABLED=1 DATA_DIR=/app/data PORT=10000
EXPOSE 10000
CMD ["python", "scripts/serve.py"]
