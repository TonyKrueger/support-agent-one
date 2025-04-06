.PHONY: help install dev test test-cov lint format clean

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  help      - Show this help message"
	@echo "  install   - Install production dependencies"
	@echo "  dev       - Install development dependencies"
	@echo "  test      - Run tests"
	@echo "  test-cov  - Run tests with coverage report"
	@echo "  lint      - Run linters"
	@echo "  format    - Format code"
	@echo "  clean     - Clean up cache files"

install:
	poetry install --no-dev

dev:
	poetry install --with dev

test:
	poetry run pytest tests/

test-cov:
	poetry run pytest tests/ --cov=app --cov-report=term --cov-report=html

lint:
	poetry run ruff check app/ tests/
	poetry run mypy app/ tests/

format:
	poetry run black app/ tests/
	poetry run isort app/ tests/

clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 