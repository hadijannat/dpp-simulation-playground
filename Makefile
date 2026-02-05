.PHONY: help up down logs restart test seed migrate clean health load-test

COMPOSE_FILE := infrastructure/docker/docker-compose.yml
COMPOSE_DEV  := infrastructure/docker/docker-compose.dev.yml

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

up: ## Start all services
	docker compose -f $(COMPOSE_FILE) up -d

up-dev: ## Start with hot-reload for development
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV) up -d

down: ## Stop all services
	docker compose -f $(COMPOSE_FILE) down

logs: ## Tail logs for all services
	docker compose -f $(COMPOSE_FILE) logs -f

restart: ## Restart all services
	docker compose -f $(COMPOSE_FILE) restart

migrate: ## Run database migrations
	./scripts/run-migrations.sh

seed: ## Seed database with initial data
	./scripts/seed-database.sh

test: ## Run all tests
	@echo "Run unit tests"

clean: ## Remove all containers and volumes
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans

health: ## Check health of all services
	./scripts/health-check.sh

load-test: ## Run load tests
	python scripts/load-test.py
