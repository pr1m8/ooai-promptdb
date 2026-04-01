PYTHONPATH ?= src
PDM ?= pdm

.PHONY: install api dashboard test unit integration e2e cov lint format typecheck docs docs-linkcheck build clean all

install:
	$(PDM) install -G dev -G test -G docs -G dashboard -G observability -G minio -G redis

api:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run uvicorn promptdb.api:app --reload

dashboard:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run streamlit run src/promptdb/dashboard_streamlit/app.py

test:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run pytest -q

unit:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run pytest -m unit -q

integration:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run pytest -m integration -q

e2e:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run pytest -m e2e -q

cov:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run pytest --cov=src/promptdb --cov-report=term-missing --cov-report=xml

lint:
	$(PDM) run ruff check .

format:
	$(PDM) run ruff format .

typecheck:
	PYTHONPATH=$(PYTHONPATH) $(PDM) run mypy src

docs:
	$(PDM) run sphinx-build --keep-going -b html docs/source docs/build/html

docs-linkcheck:
	$(PDM) run sphinx-build -W --keep-going -b linkcheck docs/source docs/build/linkcheck

build:
	$(PDM) build

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache docs/build build dist .coverage coverage.xml htmlcov
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

all: lint typecheck test docs
