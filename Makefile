.PHONY: test lint build-rps

test:
	pytest

lint:
	ruff check src tests scripts
	mypy src

build-rps:
	python scripts/build_rps.py
