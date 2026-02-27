FROM ubuntu:latest
LABEL authors="SilasKumi"

# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV ENV=production \
    SKIP_CREATE_ALL=0 \
    DATABASE_URL=postgresql+psycopg2://postgres:password@db:5432/taskr


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]