TEST_DIR := tests/
SRC_DIR := src/
ENV_PREFIX=.venv/bin/
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
	$(ENV_PREFIX)coverage run -m pytest $(TEST_DIR)
	$(ENV_PREFIX)coverage report -m
	$(ENV_PREFIX)coverage html

lint/pyright:
	$(ENV_PREFIX)pyright $(SRC_DIR)

lint/ruff:
	$(ENV_PREFIX)ruff check $(SRC_DIR)

lint: lint/pyright lint/ruff

test:
	$(ENV_PREFIX)pytest --verbose --color=yes $(TEST_DIR)

format:
	$(ENV_PREFIX)ruff format $(SRC_DIR) $(TEST_DIR)

clean-docs:
	$(ENV_PREFIX)rm -rf $(DOCS_BUILD_DIR)

docs: clean-docs
	$(ENV_PREFIX)mkdocs build --clean

serve-coverage:
	$(ENV_PREFIX)python -m http.server --directory htmlcov/ 8080

serve-docs:
	$(ENV_PREFIX)mkdocs serve
