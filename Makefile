.PHONY: install run lint build publish-check

install:
	uv sync

run:
	uv run database

lint:
	uv run ruff check .

build:
	uv build

publish-check: build
	uv publish --dry-run --trusted-publishing never
