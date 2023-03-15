##@ Juju spell

run:  ## Run

	poetry run python -m juju_spell

##@ Lint

lint:  ## Run linter
	poetry run pflake8
	poetry run pylint --recursive=y .
	poetry run black --check --diff --color .
	poetry run mypy .
	poetry run isort --check --diff --color .

lint-format:  ## Format
	poetry run black  --diff --color .
	poetry run isort  --diff --color .

.PHONY: lint lint-format

##@ Help

.PHONY: help

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
