.PHONY: help dev serve web-dev test web-test test-all lint typecheck check install

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -e ".[dev,ml]"
	cd web && npm install

serve: ## Start backend with reload
	uvicorn alertforge.api.app:app --reload --port 8000

web-dev: ## Start frontend dev server
	cd web && npm run dev

dev: ## Start backend + frontend (use start.sh for full setup)
	./start.sh

test: ## Run Python tests with coverage
	pytest --cov-fail-under=85

web-test: ## Run frontend tests
	cd web && npm test

test-all: test web-test ## Run all tests

lint: ## Run ruff linter
	ruff check src tests
	ruff format --check src tests

typecheck: ## Run mypy
	mypy

check: lint typecheck test web-test ## Run all checks

web-build: ## Build frontend for production
	cd web && npm run build
