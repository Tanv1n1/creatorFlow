.PHONY: dev batch install lint test check-env health migrate reset

install:
	pip install -e ".[dev]"

dev:
	python -m creatorflow.main

batch:
	python -m creatorflow.batch

check-env:
	python scripts/check_env.py

health:
	python scripts/health_check.py

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
