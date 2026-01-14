# Stage 1: Build Frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/dashboard

# Copy package files
COPY dashboard/package*.json ./
RUN npm install

# Copy source and build
COPY dashboard/ .
RUN npm run build

# Stage 2: Python Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed
# RUN apt-get update && apt-get install -y --no-install-recommends ...

# Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY . .

# Copy Built Frontend from Stage 1
# Ensure the destination matches where dashboard_server.py expects it ("dashboard/dist")
COPY --from=frontend-builder /app/dashboard/dist ./dashboard/dist

# Expose Port
EXPOSE 8080

# Run Server
# Zeabur defaults to PORT env var, or 8080. We need to tell uvicorn to listen on 0.0.0.0
CMD ["uvicorn", "dashboard_server:app", "--host", "0.0.0.0", "--port", "8080"]
