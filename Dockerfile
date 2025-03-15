FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY app/ ./app/

# Create and copy frontend
RUN mkdir -p frontend/static
COPY frontend/ ./frontend/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# The PORT variable will be dynamically set by Heroku
# Don't hardcode it in the Dockerfile

# Command to run the application using Uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT