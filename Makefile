TEST_DIR := tests/
SRC_DIR := src/
DOCS_SOURCE_DIR := docs/source/
DOCS_BUILD_DIR := docs/build/

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

lint/pylint:
	pylint $(SRC_DIR)

lint/black:
	black --check $(SRC_DIR)

lint: lint/pyright lint/pylint lint/black

test:
	pytest --verbose --color=yes $(TEST_DIR)

clean-docs:
	rm -rf $(DOCS_BUILD_DIR)

docs: clean-docs
	sphinx-build -b html $(DOCS_SOURCE_DIR) $(DOCS_BUILD_DIR)

serve-coverage:
	python -m http.server --directory htmlcov/ 8080

serve-docs: docs
	python -m http.server --directory $(DOCS_BUILD_DIR) 9090
