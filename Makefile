.PHONY: help install dev-install clean format lint type-check test test-watch test-cov security pre-commit run build docker-build docker-run cdk-deploy agent-deploy copilot-deploy all-checks

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := uv run python
UV := uv
PYTEST := $(UV) run pytest
RUFF := $(UV) run ruff
MYPY := $(UV) run mypy
BANDIT := $(UV) run bandit
STREAMLIT := $(UV) run streamlit

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Sake Sensei - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(UV) sync

dev-install: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(UV) sync --all-extras
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	$(UV) run pre-commit install --install-hooks
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

clean: ## Clean build artifacts and cache
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

##@ Code Quality

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	$(RUFF) format .
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(NC)"
	$(RUFF) check .
	@echo "$(GREEN)✓ Linting complete$(NC)"

lint-fix: ## Lint and auto-fix issues
	@echo "$(BLUE)Linting and fixing...$(NC)"
	$(RUFF) check --fix .
	@echo "$(GREEN)✓ Fixed lint issues$(NC)"

type-check: ## Type check with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	$(MYPY) streamlit_app backend agent --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking complete$(NC)"

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	$(BANDIT) -r streamlit_app backend agent
	@echo "$(GREEN)✓ Security scan complete$(NC)"

##@ Testing

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(PYTEST)

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	$(PYTEST) -f

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) --cov --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v

test-e2e: ## Run E2E tests only
	@echo "$(BLUE)Running E2E tests...$(NC)"
	$(PYTEST) tests/e2e/ -v

##@ Development

run: ## Run Streamlit app locally
	@echo "$(BLUE)Starting Streamlit app...$(NC)"
	$(STREAMLIT) run streamlit_app/app.py

run-agent: ## Test agent locally
	@echo "$(BLUE)Testing agent locally...$(NC)"
	cd agent && $(PYTHON) agent.py

all-checks: format lint type-check test ## Run all code quality checks
	@echo "$(GREEN)✓ All checks passed!$(NC)"

pre-commit-all: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit on all files...$(NC)"
	$(UV) run pre-commit run --all-files

##@ AWS Infrastructure

cdk-bootstrap: ## Bootstrap CDK (first time only)
	@echo "$(BLUE)Bootstrapping CDK...$(NC)"
	cd infrastructure && $(UV) run cdk bootstrap
	@echo "$(GREEN)✓ CDK bootstrapped$(NC)"

cdk-synth: ## Synthesize CDK stacks
	@echo "$(BLUE)Synthesizing CDK stacks...$(NC)"
	cd infrastructure && $(UV) run cdk synth

cdk-diff: ## Show CDK diff
	@echo "$(BLUE)Showing CDK diff...$(NC)"
	cd infrastructure && $(UV) run cdk diff

cdk-deploy: ## Deploy CDK stacks
	@echo "$(BLUE)Deploying CDK stacks...$(NC)"
	cd infrastructure && $(UV) run cdk deploy --all --require-approval never
	@echo "$(GREEN)✓ CDK stacks deployed$(NC)"

cdk-destroy: ## Destroy CDK stacks
	@echo "$(RED)Destroying CDK stacks...$(NC)"
	cd infrastructure && $(UV) run cdk destroy --all

##@ AgentCore

agent-config: ## Configure agent for Runtime
	@echo "$(BLUE)Configuring agent...$(NC)"
	cd agent && $(UV) run agentcore configure --entrypoint entrypoint.py

agent-deploy: ## Deploy agent to Runtime
	@echo "$(BLUE)Deploying agent to Runtime...$(NC)"
	cd agent && $(UV) run agentcore launch
	@echo "$(GREEN)✓ Agent deployed$(NC)"

agent-test-local: ## Test agent locally
	@echo "$(BLUE)Testing agent locally...$(NC)"
	cd agent && $(PYTEST) tests/test_agent_local.py -v

gateway-create: ## Create AgentCore Gateway
	@echo "$(BLUE)Creating AgentCore Gateway...$(NC)"
	$(PYTHON) scripts/agentcore/create_gateway.py

memory-create: ## Create AgentCore Memory
	@echo "$(BLUE)Creating AgentCore Memory...$(NC)"
	$(PYTHON) scripts/agentcore/create_memory.py

##@ Docker

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	cd streamlit_app && docker build -t sakesensei:local .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run: ## Run Docker container locally
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 8501:8501 --env-file .env sakesensei:local

docker-clean: ## Remove Docker images and containers
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	docker ps -a | grep sakesensei | awk '{print $$1}' | xargs docker rm -f 2>/dev/null || true
	docker images | grep sakesensei | awk '{print $$3}' | xargs docker rmi -f 2>/dev/null || true
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

##@ Copilot

copilot-init: ## Initialize Copilot application
	@echo "$(BLUE)Initializing Copilot...$(NC)"
	cd streamlit_app && copilot init --app sakesensei --name streamlit-app --type "Load Balanced Web Service" --dockerfile ./Dockerfile

copilot-env-init: ## Create Copilot environment
	@echo "$(BLUE)Creating Copilot environment...$(NC)"
	copilot env init --name dev --profile default --default-config

copilot-deploy: ## Deploy to ECS via Copilot
	@echo "$(BLUE)Deploying to ECS via Copilot...$(NC)"
	copilot deploy --env dev
	@echo "$(GREEN)✓ Deployed to ECS$(NC)"

copilot-status: ## Show Copilot service status
	copilot svc status --env dev

copilot-logs: ## Show Copilot service logs
	copilot svc logs --follow --env dev

##@ Database

seed-data: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(NC)"
	$(PYTHON) scripts/seed_data.py
	@echo "$(GREEN)✓ Database seeded$(NC)"

##@ CI/CD

ci-local: ## Run CI checks locally
	@echo "$(BLUE)Running CI checks locally...$(NC)"
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test
	@echo "$(GREEN)✓ All CI checks passed!$(NC)"

##@ Monitoring

logs-backend: ## Show backend Lambda logs
	@echo "$(BLUE)Fetching backend logs...$(NC)"
	aws logs tail /aws/lambda/sakesensei-recommendation --follow

logs-agent: ## Show agent logs
	@echo "$(BLUE)Fetching agent logs...$(NC)"
	aws logs tail /aws/agentcore/sakesensei-agent --follow

logs-frontend: ## Show frontend ECS logs
	@echo "$(BLUE)Fetching frontend logs...$(NC)"
	copilot svc logs --follow --env dev

##@ Utilities

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "uv: $$($(UV) --version)"
	@echo "Ruff: $$($(RUFF) --version)"
	@echo "Mypy: $$($(MYPY) --version)"

deps-outdated: ## Check for outdated dependencies
	@echo "$(BLUE)Checking for outdated dependencies...$(NC)"
	$(UV) pip list --outdated

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(UV) sync --upgrade
	@echo "$(GREEN)✓ Dependencies updated$(NC)"