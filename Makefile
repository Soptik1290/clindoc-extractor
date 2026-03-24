.PHONY: run test lint docker

# Spuštění lokálního dev serveru
run:
	uvicorn app.main:app --reload

# Spuštění testů s coverage
test:
	pytest tests/ -v --cov=app

# Instalace závislostí (včetně dev)
install:
	pip install -e ".[dev]"

# Docker build & run
docker:
	docker compose up --build

# Vyčištění cache souborů
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov *.egg-info
