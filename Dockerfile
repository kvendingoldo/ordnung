# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Install uv and ruff
RUN pip install uv ruff

# Copy project files
COPY requirements.txt ./
COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install dependencies
RUN uv pip install -r requirements.txt

ENV PYTHONPATH=/app/src

# Default entrypoint: run the file_sorter tool
ENTRYPOINT ["python", "-m", "ordnung.file_sorter"]

# Example usage:
# docker run --rm -v $(pwd):/app ordnung ./tests/data/json_input1.json --check
