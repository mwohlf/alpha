# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY . .
RUN npm install
RUN npx nx build frontend

# Stage 2: Final Python Image
FROM python:3.14.0-slim
WORKDIR /app

# Install dependencies
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python code
COPY apps/backend/ .

# Copy the built React files from Stage 1
# This matches the path you used in FastAPI app.mount()
COPY --from=frontend-builder /app/dist/apps/frontend ./dist/frontend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]