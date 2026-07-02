.PHONY: dev install lint test migrate reset

install:
	pip install -e ".[dev]"

dev:
	python -m creatorflow.main

lint:
	ruff check src tests
	mypy src

test:
	pytest tests/unit -v

test-all:
	pytest tests -v

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(msg)"

reset:
	python scripts/reset_db.py
