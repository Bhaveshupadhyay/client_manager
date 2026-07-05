FROM python:3.14-slim

# Install system dependencies (tesseract-ocr requires an apt-get update first)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set environment variables for FastEmbed/HuggingFace cache paths
ENV HF_HOME=/app/cache

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv to system Python
RUN uv pip install --system --no-cache-dir -r pyproject.toml

# ---- MODEL WARMUP STEP ----
# Copy ONLY your download script first to keep build layers cached efficiently
COPY download_models.py ./
RUN python download_models.py


COPY . .

EXPOSE 8000

CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]