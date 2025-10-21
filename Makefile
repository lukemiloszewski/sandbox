init:
	uv venv .venv --python 3.12
	uv sync --all-extras

format:
	uv run ruff check scripts --fix
	uv run ruff format scripts

deps:
	uv lock --check
	uv lock --upgrade
	uv export --format requirements.txt --output-file requirements.txt --no-hashes
