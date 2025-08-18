# syntax=docker/dockerfile:1
FROM python:3.13.7-slim

WORKDIR /app

ENV DEBIAN_FRONTEND="noninteractive" \
    PYTHONPATH="/app/src"

# Copy project files
COPY requirements.txt ./
COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "-m", "ordnung.file_sorter"]
