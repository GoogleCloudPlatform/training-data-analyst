FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project into /app
COPY . /app
WORKDIR /app

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Prepare virtual environment path
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    if [ -f pyproject.toml ]; then \
        uv sync --active; \
    elif [ -f requirements.txt ]; then \
        uv pip install -U -r requirements.txt; \
    else \
        echo "Neither pyproject.toml nor requirements.txt found" && exit 1; \
    fi

# Set host and port
ENV HOST 0.0.0.0
EXPOSE $PORT

# Run ADK API Server
CMD ["python3", "adk_app.py", "--host", "0.0.0.0", "--trace_to_cloud", "--a2a"]
