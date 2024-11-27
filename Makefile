init:
	python -m pip install -r requirements.txt -r requirements_dev.txt

format:
	python -m ruff check scripts --fix
	python -m ruff format scripts

pip:
	python -m piptools compile -o requirements.txt requirements.in
	python -m piptools compile -o requirements_dev.txt requirements_dev.in
	python -m piptools sync requirements_dev.txt requirements.txt
