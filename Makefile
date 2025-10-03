.PHONY: dev dev-fast down build ingest test-api test-web test eval clean logs

# Development (standard build with all ML packages)
dev:
	docker compose -f infra/docker-compose.yml up --build

# Development FAST (minimal build, skip ML packages - requires OpenAI API key)
dev-fast:
	@echo "⚡ Starting FAST build (requires OPENAI_API_KEY in .env)"
	docker compose -f infra/docker-compose-fast.yml up --build

down:
	docker compose -f infra/docker-compose.yml down
	docker compose -f infra/docker-compose-fast.yml down

build:
	docker compose -f infra/docker-compose.yml build

# Data ingestion
ingest:
	@echo "Ingesting documents from data/pdfs..."
	curl -X POST http://localhost:8000/ingest -H "Content-Type: application/json"

# Testing
test-api:
	cd api && pytest -v tests/

test-web:
	cd web && npm test

test: test-api test-web

# Evaluation
eval:
	docker compose -f infra/docker-compose.yml exec api python eval/run_ragas.py

# Utilities
logs:
	docker compose -f infra/docker-compose.yml logs -f

logs-api:
	docker compose -f infra/docker-compose.yml logs -f api

logs-web:
	docker compose -f infra/docker-compose.yml logs -f web

clean:
	docker compose -f infra/docker-compose.yml down -v
	rm -rf api/__pycache__ api/**/__pycache__
	rm -rf web/.next web/node_modules

# Setup
setup:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Created .env file. Please edit it with your API keys."; \
		echo ""; \
		echo "For FAST build (dev-fast), you MUST set:"; \
		echo "  OPENAI_API_KEY=sk-..."; \
		echo "  EMBEDDINGS_PROVIDER=openai"; \
	else \
		echo "✅ .env already exists."; \
	fi

# Install ML packages in running container (after dev-fast)
install-ml:
	@echo "Installing sentence-transformers in running container..."
	docker compose -f infra/docker-compose-fast.yml exec api pip install --default-timeout=600 sentence-transformers==2.3.1
	@echo "✅ Done! Now you can use EMBEDDINGS_PROVIDER=local"

# Health check
health:
	@echo "Checking Qdrant..."
	@curl -s http://localhost:6333/health || echo "Qdrant not responding"
	@echo "\nChecking API..."
	@curl -s http://localhost:8000/health || echo "API not responding"
	@echo "\nChecking Web..."
	@curl -s http://localhost:3000 > /dev/null && echo "Web is up" || echo "Web not responding"


