# docker/Dockerfile

# Stage 1: Builder Stage
FROM python:3.11-slim as builder

# Metadata
LABEL maintainer="devops-team@blockchain-voting.com" \
      description="Multi-stage Dockerfile for Blockchain-Based Decentralized Voting Platform" \
      version="1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy only dependency files to leverage Docker caching
COPY pyproject.toml poetry.lock ./

# Install dependencies in a virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main \
    && rm -rf ~/.cache/pip

# Stage 2: Runtime Stage
FROM python:3.11-slim as runtime

# Metadata
LABEL maintainer="devops-team@blockchain-voting.com" \
      description="Runtime image for Blockchain-Based Decentralized Voting Platform" \
      version="1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Create a non-root user
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi7 \
    libssl1.1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR $APP_HOME

# Copy application code from builder stage
COPY --from=builder /app /app

# Set proper permissions
RUN chown -R appuser:appuser $APP_HOME

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint
ENTRYPOINT ["python", "-m", "app.main"]