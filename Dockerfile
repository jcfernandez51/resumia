# syntax=docker/dockerfile:1

# Vite convierte el frontend en archivos HTML, CSS y JavaScript.
FROM node:20-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./

# Esta clave es publica y Vite la necesita durante la compilacion.
ARG VITE_CLERK_PUBLISHABLE_KEY
RUN test -n "$VITE_CLERK_PUBLISHABLE_KEY" && npm run build

# Un solo contenedor ejecuta FastAPI y sirve el frontend compilado.
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt uvicorn==0.34.0
COPY backend/app ./backend/app
COPY --from=frontend /build/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["uvicorn", "backend.app.docker:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
