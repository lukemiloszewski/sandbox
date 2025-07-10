init:
	uv venv .venv --python 3.12
	uv sync --all-extras

format:
	uv run ruff check src tests --fix
	uv run ruff format src tests

deps:
	uv lock --check
	uv lock --upgrade
	uv export --format requirements.txt --output-file requirements.txt --no-hashes
