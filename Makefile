APP_NAME := freelancer
ENV_FILE := .env
DOCKER_COMPOSE := docker compose -f infrastructure/compose/docker-compose.yml
PYTHON := uv run python
UV := uv

# --- Environment Setup ---
.PHONY: bootstrap
bootstrap:
	@echo "🚀 Bootstrapping development environment..."
	@$(UV) install
	@bash scripts/bootstrap.sh
	@bash scripts/minio_bootstrap.sh
	@echo "✅ Environment ready."

.PHONY: env
env:
	@cp -n .env.example .env || true
	@echo "✅ .env file prepared."

# --- Database Management ---
.PHONY: db-upgrade db-downgrade db-seed db-refresh
db-upgrade:
	@echo "📦 Applying Alembic migrations..."
	@$(PYTHON) -m alembic upgrade head

db-downgrade:
	@echo "⚙️  Rolling back Alembic migrations..."
	@$(PYTHON) -m alembic downgrade -1

db-seed:
	@echo "🌱 Seeding initial data..."
	@bash migrations/seed_data.sh

db-refresh:
	@echo "🔄 Refreshing database..."
	@bash migrations/refresh.sh

# --- Docker / Infrastructure ---
.PHONY: build up down logs ps shell
build:
	@echo "🐳 Building FastApp Docker images..."
	@$(DOCKER_COMPOSE) build

up:
	@echo "⬆️  Starting FastApp stack..."
	@$(DOCKER_COMPOSE) up -d

down:
	@echo "⬇️  Stopping FastApp stack..."
	@$(DOCKER_COMPOSE) down

logs:
	@$(DOCKER_COMPOSE) logs -f

ps:
	@$(DOCKER_COMPOSE) ps

shell:
	@$(DOCKER_COMPOSE) exec web bash

# --- MinIO / S3 ---
.PHONY: minio-setup minio-cleanup minio-reset
minio-setup:
	@bash scripts/minio_bootstrap.sh

minio-cleanup:
	@bash scripts/minio_bootstrap.sh --cleanup-only

minio-reset:
	@bash scripts/minio_bootstrap.sh --reset-bucket

# --- Tests ---
.PHONY: test test-async test-e2e
test:
	@echo "🧪 Running unit and integration tests..."
	@$(UV) run pytest -q --disable-warnings -m "not async"

test-async:
	@echo "⚡ Running async tests..."
	@$(UV) run pytest -q -m async --disable-warnings

test-e2e:
	@echo "🧩 Running full end-to-end test suite..."
	@$(UV) run pytest tests/test_end_to_end.py -q --disable-warnings

# --- Performance / Load Testing ---
.PHONY: perf-test perf-scale perf-down
perf-test:
	@echo "🏎️  Launching Locust in standalone mode..."
	@$(UV) run locust -f tests/performance/locustfile.py --host http://localhost:8000

perf-scale:
	@echo "🌐 Launching distributed Locust environment..."
	@docker compose -f tests/performance/docker-compose.locust.yml up --scale locust-worker=4 -d
	@echo "✅ Access Locust UI at http://localhost:8089"

perf-down:
	@docker compose -f tests/performance/docker-compose.locust.yml down
	@echo "🧹 Stopped distributed Locust environment."

# --- Infrastructure (Terraform / Lightsail) ---
.PHONY: infra-init infra-apply infra-destroy lightsail-deploy
infra-init:
	@echo "⚙️  Initializing Terraform..."
	@cd infrastructure/terraform && terraform init

infra-apply:
	@echo "🚀 Applying Terraform configuration..."
	@cd infrastructure/terraform && terraform apply -auto-approve

infra-destroy:
	@echo "🔥 Destroying Terraform resources..."
	@cd infrastructure/terraform && terraform destroy -auto-approve

lightsail-deploy:
	@echo "☁️  Deploying FastApp to AWS Lightsail..."
	@bash infrastructure/aws/deploy_lightsail.sh

# --- Monitoring / Observability ---
.PHONY: monitor-up monitor-down
monitor-up:
	@docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml up -d
	@echo "📊 Monitoring stack started (Grafana, Prometheus)."

monitor-down:
	@docker compose -f infrastructure/monitoring/docker-compose.monitoring.yml down

# --- Cleanup ---
.PHONY: clean
clean:
	@echo "🧹 Cleaning temporary and cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache logs/* || true
	@echo "✅ Clean complete."

# --- Default Help ---
.PHONY: help
help:
	@echo "Available Make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# --- CI/CD Makefile Targets ---

.PHONY: ci-test ci-validate ci-deploy
ci-test:
	@echo "🧪 Running full CI test pipeline locally..."
	@make lint
	@make test
	@make test-async
	@make test-e2e

ci-validate:
	@echo "⚙️  Validating Docker and Terraform integrity..."
	docker build -f infrastructure/docker/Dockerfile .
	cd infrastructure/terraform && terraform init -backend=false && terraform validate
	@echo "✅ Validation complete."

ci-deploy:
	@echo "🚀 Deploying FastApp via Makefile (CI equivalent)..."
	@docker build -t fastapp:latest -f infrastructure/docker/Dockerfile .
	@docker tag fastapp:latest $$(aws ecr describe-repositories --repository-names fastapp --query 'repositories[0].repositoryUri' --output text):latest
	@docker push $$(aws ecr describe-repositories --repository-names fastapp --query 'repositories[0].repositoryUri' --output text):latest
	@make lightsail-deploy
	@echo "✅ Deployment complete."

# ---------------------------------------------------------------------
# Monitoring and Observability
# ---------------------------------------------------------------------

monitor-up:
	@echo "🚀 Starting FastApp Monitoring Stack (Prometheus + Grafana)..."
	docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/monitoring/docker-compose.override.yml up -d prometheus grafana
	@echo "✅ Monitoring stack is up."
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana:    http://localhost:3000 (default admin/admin)"

monitor-down:
	@echo "🛑 Stopping FastApp Monitoring Stack..."
	docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/monitoring/docker-compose.override.yml down

monitor-logs:
	@echo "📜 Tail Grafana + Prometheus logs..."
	docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/monitoring/docker-compose.override.yml logs -f grafana prometheus

monitor-restart:
	@echo "🔄 Restarting FastApp Monitoring Stack..."
	make monitor-down
	sleep 2
	make monitor-up
	
	
monitor-import:
	@echo "📥 Importing Grafana dashboards..."
	python scripts/import_grafana_dashboards.py
	
# ---------------------------------------------------------------------
# Monitoring Stack (Prometheus + Grafana)
# ---------------------------------------------------------------------

monitor-up:
	@echo "🚀 Starting FastApp Monitoring Stack (Prometheus + Grafana)..."
	docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/monitoring/docker-compose.override.yml up -d prometheus grafana
	@echo "⏳ Waiting for Grafana to initialize..."
	sleep 10
	@echo "📥 Importing dashboards into Grafana..."
	python scripts/import_grafana_dashboards.py || echo "⚠️ Dashboard import skipped or failed."
	@echo "✅ Monitoring stack is up."
	@echo "   - Prometheus: http://localhost:9090"
	@echo "   - Grafana:    http://localhost:3000 (admin/admin)"

monitor-down:
	@echo "🛑 Stopping FastApp Monitoring Stack..."
	docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/monitoring/docker-compose.override.yml down

monitor-logs:
	@echo "📜 Tail Grafana + Prometheus logs..."
	docker compose -f infrastructure/compose/docker-compose.yml -f infrastructure/monitoring/docker-compose.override.yml logs -f grafana prometheus

monitor-restart:
	@echo "🔄 Restarting FastApp Monitoring Stack..."
	make monitor-down
	sleep 2
	make monitor-up