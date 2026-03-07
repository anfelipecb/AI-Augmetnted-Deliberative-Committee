# HPIC Committee — Streamlit app with UV
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock ./
ENV UV_NO_DEV=1
RUN uv sync --locked --no-install-project

# Copy application (README.md required by pyproject.toml for hatchling build)
COPY README.md ./
COPY src/ src/
COPY agents/ agents/
COPY app.py ./
COPY .streamlit/ .streamlit/
COPY docs/ docs/

RUN uv sync --locked

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
