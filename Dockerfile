# syntax=docker/dockerfile:1

# --- builder: production dependencies installed with uv ---------------------------
FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, so this layer is reused while only the code changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# --- runtime: only the virtual environment and the code, as a non-root user ---------
FROM python:3.14-slim AS runtime

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini ./
COPY migrations ./migrations

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 8000
CMD ["uvicorn", "app.entrypoints.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- test: development dependencies and the test suite ------------------------------
FROM builder AS test

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

COPY alembic.ini pytest.ini .flake8 ./
COPY migrations ./migrations
COPY tests ./tests

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

CMD ["pytest"]
