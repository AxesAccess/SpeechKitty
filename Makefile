.PHONY: install test lint format clean

install:
	pip install -e .[dev]

test:
	pytest --cov=app --cov-report=term-missing

lint:
	flake8 app tests
	mypy app tests

format:
	black app tests
	isort app tests

clean:
	rm -rf build dist *.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
