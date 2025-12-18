FROM python:3.11-slim

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files and README
COPY pyproject.toml poetry.lock README.md ./

# Copy source code
COPY src/ ./src/

# Install dependencies (no dev dependencies, no virtualenv in container)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# Set the entrypoint
ENTRYPOINT ["python", "-m", "slice_oas"]

# Default command shows help
CMD ["--help"]
