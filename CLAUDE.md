# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Build a production-grade AI Agent on AWS (translated from an ML-Architects Azure tutorial). The agent:
- Answers questions about a website via RAG (OpenSearch Serverless)
- Drafts emails and converts currencies via tool use (LangChain)
- Is fully observable (CloudWatch + OpenTelemetry → X-Ray)

## Architecture

| Component | Technology | Notes |
|-----------|-----------|-------|
| Orchestration | AWS EKS (t3.medium) | Runs the LangChain Python app — NOT the model |
| Models | AWS Bedrock (Claude Haiku) | Serverless API, no GPU on EKS nodes |
| Vector DB | Amazon OpenSearch Serverless | VECTORSEARCH type, RAG retrieval |
| Container Registry | Amazon ECR | |
| Secrets | AWS Secrets Manager | `recovery_window_in_days = 0` for clean destroy |
| Observability | CloudWatch Logs + OpenTelemetry | OTLP → AWS X-Ray |
| Region | eu-central-1 (Frankfurt) | Swiss data residency |

## Terraform Commands

All infrastructure lives in `/terraform`. Work from that directory.

```bash
cd terraform/
terraform init        # Download providers/modules (first time or after provider changes)
terraform validate    # Check HCL syntax
terraform fmt         # Format HCL files
terraform plan        # Dry-run — read-only, no AWS cost
terraform apply       # Provision infrastructure
terraform destroy     # Tear down everything (run between sessions — zero cost at rest)
```

## Terraform File Map

| File | Purpose |
|------|---------|
| `provider.tf` | AWS provider locked to `~> 5.0`, region `eu-central-1` |
| `variables.tf` | Region, environment, cluster name |
| `network.tf` | VPC (`10.0.0.0/16`), 2 private + 2 public subnets, single NAT Gateway |
| `iam.tf` | EKS cluster role + node role, least-privilege (ECR, CloudWatch, CNI) |
| `main.tf` | EKS cluster, node group (t3.medium, 1–2 nodes), ECR repo, Secrets Manager |
| `vector_db.tf` | OpenSearch Serverless collection, access/security/encryption policies |

## Key Engineering Decisions

- **t3.medium is intentional** — the model runs on Bedrock (serverless API), not on EKS nodes
- **`single_nat_gateway = true`** — saves ~$30/month vs. one NAT Gateway per AZ
- **`recovery_window_in_days = 0`** on Secrets Manager — forces immediate deletion on `terraform destroy`, avoiding a 7-day wait that blocks re-creation
- **`terraform destroy` between sessions** — this is a dev portfolio; run destroy to incur zero cost at rest

## Next Steps (as of project start)

1. `terraform init` → download providers
2. `terraform plan` → dry-run against AWS
3. Build the Python Agent: LangChain app → Docker → ECR → EKS via Helm

## Application Stack (when built)

- **Python / LangChain** — agent logic, tool use, RAG orchestration
- **LlamaIndex** — document indexing alternative
- **AWS Bedrock** — LLM inference (Claude Haiku, Titan Embeddings)
- **boto3** — AWS SDK
- **OpenTelemetry** — distributed tracing (OTLP exporter → X-Ray)
- **RAGAS** — RAG evaluation framework

## Engineering Principles

All code in this repository follows these principles:

- **MLOps best practices** — reproducible pipelines, versioned artifacts, automated model evaluation, continuous training/deployment, monitoring in production
- **Domain-Driven Design (DDD)** — model the ML domain explicitly (ingestion, embedding, retrieval, inference are distinct bounded contexts); use ubiquitous language from the ML/Pharma domain
- **Clean Architecture** — separate domain logic from infrastructure concerns; application code must not depend directly on AWS SDK or LangChain internals — use ports and adapters (interfaces/abstract classes) to invert those dependencies
- **Infrastructure as Code** — all AWS resources are defined in Terraform; no manual console changes; environments are reproducible and disposable
- **Clean Code** — meaningful names, small focused functions/classes, no dead code, explicit over implicit

## Domain Context

This portfolio targets **ML Infrastructure Engineering** roles in Basel Pharma. Relevant compliance context: GxP, 21 CFR Part 11, Swiss nLPD (data residency → eu-central-1).
