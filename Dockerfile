# Start with a small image that contains Python 3.14.10.
FROM python:3.14.10-slim

# Copy uv into the image so it can install the project's Python packages.
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

# Use /app as the folder for the project inside the image.
WORKDIR /app

# Copy the package list and lock file first, so Docker can reuse the install when app code changes.
COPY pyproject.toml uv.lock README.md ./

# Install the locked main packages without installing the app or development packages yet.
RUN uv sync --locked --no-dev --no-install-project

# Copy the database migration settings and files needed to update the database layout.
COPY alembic.ini ./
COPY migrations ./migrations

# Copy the scripts used to seed demo data and index the knowledge base.
COPY scripts ./scripts

# Copy the Python code and fictional knowledge base into the image.
COPY src ./src
COPY CLEARANCE_SYNTHETIC_KNOWLEDGE_BASE.md ./

# Install Clearance itself, using the packages already installed above.
RUN uv sync --locked --no-dev --no-editable

# Record that the API listens on port 8000 inside this image.
EXPOSE 8000

# Start the API and allow connections from outside this container.
CMD ["uv", "run", "--no-sync", "fastapi", "run", "src/clearance/main.py", "--host", "0.0.0.0", "--port", "8000"]
