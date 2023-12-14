TEST_DIR := tests/
SRC_DIR := src/
DOCS_SOURCE_DIR := docs/
DOCS_BUILD_DIR := site/

clean: clean-build clean-pyc clean-test clean-cache

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

clean-cache:
	rm -fr .mypy_cache
	rm -fr .pytest_cache

coverage:
	coverage run -m pytest $(TEST_DIR)
	coverage report -m
	coverage html

lint/pyright:
	pyright $(SRC_DIR)

lint/ruff:
	ruff $(SRC_DIR)

lint/black:
	black --check $(SRC_DIR)

lint: lint/pyright lint/ruff lint/black

test:
	pytest --verbose --color=yes $(TEST_DIR)

format:
	black $(SRC_DIR) $(TEST_DIR)
	isort $(SRC_DIR) $(TEST_DIR)

clean-docs:
	rm -rf $(DOCS_BUILD_DIR)

docs: clean-docs
	mkdocs build --clean

serve-coverage:
	python -m http.server --directory htmlcov/ 8080

serve-docs:
	mkdocs serve
