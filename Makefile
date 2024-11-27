init:
	python -m pip install -r requirements.txt -r requirements_dev.txt

format:
	python -m ruff check scripts --fix --exclude '*.ipynb'
	python -m ruff format scripts --exclude '*.ipynb'

pip:
	python -m piptools compile -o requirements.txt requirements.in
	python -m piptools compile -o requirements_dev.txt requirements_dev.in
	python -m piptools sync requirements_dev.txt requirements.txt
