.PHONY: install lint test up down migrate revision fmt

install:
	pip install -e ".[dev]"

lint:
	ruff check app tools tests alembic
	ruff format --check app tools tests alembic

fmt:
	ruff format app tools tests alembic
	ruff check --fix app tools tests alembic

test:
	pytest -q

up:
	docker compose up --build -d

down:
	docker compose down

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"
