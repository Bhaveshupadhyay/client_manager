FROM python:3.14-slim

RUN apt-get install tesseract-ocr
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv to system Python
RUN uv pip install --system --no-cache-dir .

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]