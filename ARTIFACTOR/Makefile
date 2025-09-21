# ARTIFACTOR v3.0 - Enterprise Development and Deployment Makefile
# Comprehensive build, test, and deployment automation

.PHONY: help build test deploy clean dev prod monitoring backup

# =====================================
# CONFIGURATION
# =====================================

PROJECT_NAME := artifactor
VERSION := 3.0.0
DOCKER_REGISTRY := artifactor
ENVIRONMENT := development

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

# =====================================
# HELP
# =====================================

help: ## Show this help message
	@echo "$(CYAN)ARTIFACTOR v$(VERSION) - Enterprise Claude.ai Artifact Management Platform$(NC)"
	@echo ""
	@echo "$(YELLOW)Available Commands:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  $(GREEN)make dev$(NC)          - Start development environment"
	@echo "  $(GREEN)make prod$(NC)         - Start production environment"
	@echo "  $(GREEN)make test$(NC)         - Run all tests"
	@echo "  $(GREEN)make clean$(NC)        - Clean up everything"

# =====================================
# ENVIRONMENT SETUP
# =====================================

setup: ## Initial project setup
	@echo "$(BLUE)Setting up ARTIFACTOR v$(VERSION)...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file from template...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env file created$(NC)"; \
	else \
		echo "$(GREEN)✓ .env file already exists$(NC)"; \
	fi
	@mkdir -p downloads uploads models logs database/backups
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(GREEN)✓ Setup complete!$(NC)"

env-dev: ## Copy development environment file
	@cp .env.example .env
	@sed -i 's/ENVIRONMENT=development/ENVIRONMENT=development/g' .env
	@sed -i 's/DEBUG=false/DEBUG=true/g' .env
	@echo "$(GREEN)✓ Development environment configured$(NC)"

env-prod: ## Copy production environment file
	@cp .env.example .env
	@sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/g' .env
	@sed -i 's/DEBUG=true/DEBUG=false/g' .env
	@echo "$(YELLOW)⚠ Remember to update production secrets in .env$(NC)"

# =====================================
# DEVELOPMENT
# =====================================

dev: setup ## Start development environment
	@echo "$(BLUE)Starting ARTIFACTOR v$(VERSION) development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml up --build -d
	@echo "$(GREEN)✓ Development environment started$(NC)"
	@echo ""
	@echo "$(CYAN)Development Services:$(NC)"
	@echo "  Frontend:     http://localhost:3000"
	@echo "  Backend API:  http://localhost:8000"
	@echo "  API Docs:     http://localhost:8000/api/v1/docs"
	@echo "  PgAdmin:      http://localhost:5050"
	@echo "  Redis UI:     http://localhost:8081"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Grafana:      http://localhost:3001"

dev-logs: ## Show development logs
	docker-compose -f docker-compose.dev.yml logs -f

dev-stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	@echo "$(GREEN)✓ Development environment stopped$(NC)"

dev-restart: ## Restart development environment
	@echo "$(YELLOW)Restarting development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml restart
	@echo "$(GREEN)✓ Development environment restarted$(NC)"

dev-rebuild: ## Rebuild and restart development environment
	@echo "$(YELLOW)Rebuilding development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up --build -d
	@echo "$(GREEN)✓ Development environment rebuilt$(NC)"

# =====================================
# PRODUCTION
# =====================================

prod: setup ## Start production environment
	@echo "$(BLUE)Starting ARTIFACTOR v$(VERSION) production environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)✗ .env file not found. Run 'make env-prod' first$(NC)"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.prod.yml up --build -d
	@echo "$(GREEN)✓ Production environment started$(NC)"
	@echo ""
	@echo "$(CYAN)Production Services:$(NC)"
	@echo "  Application:  http://localhost:80"
	@echo "  HTTPS:        https://localhost:443"
	@echo "  Monitoring:   http://localhost:3001"

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

prod-stop: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml down
	@echo "$(GREEN)✓ Production environment stopped$(NC)"

prod-scale: ## Scale production services
	@echo "$(BLUE)Scaling production services...$(NC)"
	docker-compose -f docker-compose.prod.yml up --scale backend=3 --scale frontend=2 --scale worker=3 -d
	@echo "$(GREEN)✓ Services scaled$(NC)"

# =====================================
# BUILDING
# =====================================

build: ## Build all Docker images
	@echo "$(BLUE)Building ARTIFACTOR v$(VERSION) images...$(NC)"
	docker-compose -f docker-compose.enterprise.yml build --parallel
	@echo "$(GREEN)✓ All images built$(NC)"

build-backend: ## Build backend image
	@echo "$(BLUE)Building backend image...$(NC)"
	docker build -f backend/Dockerfile -t $(DOCKER_REGISTRY)/artifactor-backend:$(VERSION) .
	@echo "$(GREEN)✓ Backend image built$(NC)"

build-frontend: ## Build frontend image
	@echo "$(BLUE)Building frontend image...$(NC)"
	docker build -f frontend/Dockerfile -t $(DOCKER_REGISTRY)/artifactor-frontend:$(VERSION) .
	@echo "$(GREEN)✓ Frontend image built$(NC)"

build-ml: ## Build ML service image
	@echo "$(BLUE)Building ML service image...$(NC)"
	docker build -f ml-service/Dockerfile -t $(DOCKER_REGISTRY)/artifactor-ml-service:$(VERSION) .
	@echo "$(GREEN)✓ ML service image built$(NC)"

build-nginx: ## Build nginx image
	@echo "$(BLUE)Building nginx image...$(NC)"
	docker build -f nginx/Dockerfile -t $(DOCKER_REGISTRY)/artifactor-nginx:$(VERSION) .
	@echo "$(GREEN)✓ Nginx image built$(NC)"

# =====================================
# TESTING
# =====================================

test: ## Run all tests
	@echo "$(BLUE)Running ARTIFACTOR v$(VERSION) tests...$(NC)"
	@make test-backend
	@make test-frontend
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend pytest tests/ -v --cov=app --cov-report=term-missing
	@echo "$(GREEN)✓ Backend tests completed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	docker-compose -f docker-compose.dev.yml exec frontend npm test -- --coverage --watchAll=false
	@echo "$(GREEN)✓ Frontend tests completed$(NC)"

test-ml: ## Run ML service tests
	@echo "$(BLUE)Running ML service tests...$(NC)"
	docker-compose -f docker-compose.dev.yml exec ml-service pytest tests/ -v
	@echo "$(GREEN)✓ ML service tests completed$(NC)"

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend pytest tests/integration/ -v
	@echo "$(GREEN)✓ Integration tests completed$(NC)"

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running E2E tests...$(NC)"
	docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e
	@echo "$(GREEN)✓ E2E tests completed$(NC)"

# =====================================
# CODE QUALITY
# =====================================

lint: ## Run linting on all code
	@echo "$(BLUE)Running linting...$(NC)"
	@make lint-backend
	@make lint-frontend
	@echo "$(GREEN)✓ Linting completed$(NC)"

lint-backend: ## Run backend linting
	@echo "$(BLUE)Linting backend code...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend flake8 app/
	docker-compose -f docker-compose.dev.yml exec backend black --check app/
	docker-compose -f docker-compose.dev.yml exec backend isort --check-only app/
	@echo "$(GREEN)✓ Backend linting completed$(NC)"

lint-frontend: ## Run frontend linting
	@echo "$(BLUE)Linting frontend code...$(NC)"
	docker-compose -f docker-compose.dev.yml exec frontend npm run lint:check
	@echo "$(GREEN)✓ Frontend linting completed$(NC)"

format: ## Format all code
	@echo "$(BLUE)Formatting code...$(NC)"
	@make format-backend
	@make format-frontend
	@echo "$(GREEN)✓ Code formatting completed$(NC)"

format-backend: ## Format backend code
	@echo "$(BLUE)Formatting backend code...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend black app/
	docker-compose -f docker-compose.dev.yml exec backend isort app/
	@echo "$(GREEN)✓ Backend formatting completed$(NC)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	docker-compose -f docker-compose.dev.yml exec frontend npm run format
	@echo "$(GREEN)✓ Frontend formatting completed$(NC)"

# =====================================
# DATABASE
# =====================================

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
	@echo "$(GREEN)✓ Database migrations completed$(NC)"

db-reset: ## Reset database
	@echo "$(YELLOW)⚠ This will destroy all data. Are you sure? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@echo "$(BLUE)Resetting database...$(NC)"
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.dev.yml up -d postgres redis
	@sleep 10
	@make db-migrate
	@echo "$(GREEN)✓ Database reset completed$(NC)"

db-backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p database/backups
	docker-compose -f docker-compose.dev.yml exec postgres pg_dump -U artifactor -d artifactor > database/backups/backup-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "$(GREEN)✓ Database backup created$(NC)"

db-restore: ## Restore database from backup
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -la database/backups/
	@echo "$(YELLOW)Enter backup filename:$(NC)" && read backup && \
	docker-compose -f docker-compose.dev.yml exec -T postgres psql -U artifactor -d artifactor < database/backups/$$backup
	@echo "$(GREEN)✓ Database restored$(NC)"

# =====================================
# MONITORING
# =====================================

monitoring: ## Start monitoring stack
	@echo "$(BLUE)Starting monitoring stack...$(NC)"
	docker-compose -f docker-compose.dev.yml --profile monitoring up -d
	@echo "$(GREEN)✓ Monitoring stack started$(NC)"
	@echo ""
	@echo "$(CYAN)Monitoring Services:$(NC)"
	@echo "  Prometheus:   http://localhost:9090"
	@echo "  Grafana:      http://localhost:3001"

logs: ## Show application logs
	@echo "$(BLUE)Showing application logs...$(NC)"
	docker-compose logs -f --tail=100

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo "$(CYAN)Backend Health:$(NC)"
	@curl -s http://localhost:8000/health | jq . || echo "Backend not available"
	@echo ""
	@echo "$(CYAN)ML Service Health:$(NC)"
	@curl -s http://localhost:8001/health | jq . || echo "ML Service not available"

status: ## Show service status
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose -f docker-compose.dev.yml ps

# =====================================
# DEPLOYMENT
# =====================================

deploy-staging: ## Deploy to staging
	@echo "$(BLUE)Deploying to staging...$(NC)"
	@./scripts/deploy.sh staging
	@echo "$(GREEN)✓ Staging deployment completed$(NC)"

deploy-prod: ## Deploy to production
	@echo "$(BLUE)Deploying to production...$(NC)"
	@./scripts/deploy.sh production
	@echo "$(GREEN)✓ Production deployment completed$(NC)"

# =====================================
# MAINTENANCE
# =====================================

clean: ## Clean up everything
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@echo "$(YELLOW)This will remove all containers, images, and volumes. Continue? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans
	docker-compose -f docker-compose.enterprise.yml down -v --remove-orphans
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-dev: ## Clean development environment
	@echo "$(YELLOW)Cleaning development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	@echo "$(GREEN)✓ Development cleanup completed$(NC)"

clean-prod: ## Clean production environment
	@echo "$(YELLOW)Cleaning production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml down -v --remove-orphans
	@echo "$(GREEN)✓ Production cleanup completed$(NC)"

update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	@make update-backend
	@make update-frontend
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

update-backend: ## Update backend dependencies
	@echo "$(BLUE)Updating backend dependencies...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend pip install --upgrade -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies updated$(NC)"

update-frontend: ## Update frontend dependencies
	@echo "$(BLUE)Updating frontend dependencies...$(NC)"
	docker-compose -f docker-compose.dev.yml exec frontend npm update
	@echo "$(GREEN)✓ Frontend dependencies updated$(NC)"

# =====================================
# UTILITIES
# =====================================

shell-backend: ## Open backend shell
	docker-compose -f docker-compose.dev.yml exec backend bash

shell-frontend: ## Open frontend shell
	docker-compose -f docker-compose.dev.yml exec frontend bash

shell-db: ## Open database shell
	docker-compose -f docker-compose.dev.yml exec postgres psql -U artifactor -d artifactor

shell-redis: ## Open Redis shell
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	docker-compose -f docker-compose.dev.yml exec backend sphinx-build -b html docs/ docs/_build/
	@echo "$(GREEN)✓ Documentation generated$(NC)"

validate: ## Validate Docker Compose files
	@echo "$(BLUE)Validating Docker Compose files...$(NC)"
	docker-compose -f docker-compose.dev.yml config --quiet
	docker-compose -f docker-compose.prod.yml config --quiet
	docker-compose -f docker-compose.enterprise.yml config --quiet
	@echo "$(GREEN)✓ All Docker Compose files are valid$(NC)"

# =====================================
# SECURITY
# =====================================

security-scan: ## Run security scans
	@echo "$(BLUE)Running security scans...$(NC)"
	@echo "$(YELLOW)Scanning Docker images...$(NC)"
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image $(DOCKER_REGISTRY)/artifactor-backend:$(VERSION)
	@echo "$(GREEN)✓ Security scan completed$(NC)"

# =====================================
# DEFAULT TARGET
# =====================================

.DEFAULT_GOAL := help