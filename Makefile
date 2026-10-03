.PHONY: help install up down logs test test-local lint format typecheck migrate

help:  ## Show the available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-12s %s\n", $$1, $$2}'

install:  ## Create the virtual environment and install the git hooks
	uv sync
	uv run pre-commit install

up:  ## Start database, migrations and API (http://localhost:8000/docs)
	docker compose up --build -d

down:  ## Stop every container
	docker compose --profile test down

logs:  ## Follow the API logs (simulated emails show up here)
	docker compose logs -f api

test:  ## Run the whole test suite inside Docker
	docker compose run --rm --build tests

test-local:  ## Run the test suite locally against the db-test container
	docker compose --profile test up -d --wait db-test
	uv run pytest

lint:  ## Check formatting, imports, style and types
	uv run black --check .
	uv run isort --check-only .
	uv run flake8 .
	uv run mypy

format:  ## Format the code with black and isort
	uv run black .
	uv run isort .

migrate:  ## Apply migrations to the local database
	uv run alembic upgrade head
