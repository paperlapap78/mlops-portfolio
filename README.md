# MLOps Portfolio — Production AI Agent on AWS

A production-grade AI Agent built on AWS, following Clean Architecture and MLOps best practices. The agent answers questions about a website via RAG, drafts emails, and converts currencies — fully observable via CloudWatch and OpenTelemetry.

## Architecture

```
User Request
     │
     ▼
FastAPI (EKS / t3.medium)
     │
     ├── POST /ingest   → Scrape URL → LangChain chunking → Bedrock Titan embeddings → OpenSearch
     ├── POST /query    → Embed question → OpenSearch similarity search → Bedrock Claude → Answer
     └── POST /agent    → LangChain tool-use agent (email drafting, currency conversion)
```

| Component | Technology |
|-----------|-----------|
| Orchestration | AWS EKS (t3.medium) — runs the Python app, not the model |
| LLM & Embeddings | AWS Bedrock (Claude Haiku + Titan Embeddings v2) |
| Vector DB | Amazon OpenSearch Serverless (VECTORSEARCH) |
| Container Registry | Amazon ECR |
| Secrets | AWS Secrets Manager |
| Observability | structlog + OpenTelemetry → CloudWatch / X-Ray |
| Region | eu-central-1 (Frankfurt — Swiss data residency) |
| IaC | Terraform |
| CI/CD | GitHub Actions (lint → test → build → ECR push) |

## Project Structure

```
├── agent/                  Python application
│   ├── src/agent/
│   │   ├── domain/         Pure Python models and port interfaces (no external deps)
│   │   ├── application/    Use cases: ingestion, retrieval, generation
│   │   └── infrastructure/ Adapters: Bedrock, OpenSearch, LangChain, FastAPI
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
└── terraform/              AWS infrastructure as code
```

## Engineering Principles

- **Clean Architecture** — domain logic never imports AWS SDK or LangChain; ports and adapters invert all infrastructure dependencies
- **Domain-Driven Design** — ingestion, retrieval, and generation are distinct bounded contexts
- **MLOps best practices** — reproducible infrastructure, versioned artifacts, observability at every layer
- **Infrastructure as Code** — all AWS resources in Terraform; no manual console changes

## Local Development

```bash
# 1. Provision AWS infrastructure
cd terraform/
terraform init && terraform apply
terraform output opensearch_endpoint   # copy this value

# 2. Configure local environment
cd ../agent
cp .env.example .env
# Set OPENSEARCH_ENDPOINT in .env to the value from step 1

# 3. Install and run
pip install -e ".[dev]"
uvicorn agent.infrastructure.api.main:app --reload --port 8000

# 4. Test the endpoints
curl localhost:8000/health
curl -X POST localhost:8000/ingest -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
curl -X POST localhost:8000/query  -H "Content-Type: application/json" \
     -d '{"question": "What is this site about?"}'

# 5. Tear down (zero cost at rest)
cd ../terraform && terraform destroy
```

## Running Tests

```bash
cd agent
pytest tests/unit/ --cov=src/agent/domain --cov=src/agent/application -v
```

## CI/CD

GitHub Actions runs on every push to `main`:
1. `ruff` — linting
2. `mypy` — static type checking
3. `pytest` — unit tests with 70% coverage gate on domain and application layers
4. Docker build + push to ECR (on merge to `main` only, via GitHub OIDC — no stored AWS keys)
