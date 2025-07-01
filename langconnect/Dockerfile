FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY pyproject.toml uv.lock ./

# Copy application code (needs to be done before pip install .[dev])
COPY . .

# Install build dependencies and runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libpq-dev curl && \
    pip install --no-cache-dir pip -U && \
    pip install --no-cache-dir hatch && \
    pip install --no-cache-dir '.[dev]' && \
    # Purge build-only dependencies
    apt-get purge -y --auto-remove gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Expose the application port
EXPOSE 8080

# Command to run the application
CMD ["uv", "run", "uvicorn", "langconnect.server:APP", "--host", "0.0.0.0", "--port", "8080"]
