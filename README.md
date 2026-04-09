# AlertForge

Outcome-aware follow-up prioritization for LSST alert streams. AlertForge sits downstream of existing Rubin Observatory alert brokers (Fink, ALeRCE, ANTARES, Lasair), consumes their classifications, and ranks alerts by expected scientific return using a continuous learning loop trained on follow-up outcomes.

See [PLAN.md](PLAN.md) for the full project plan.

## Quick Start

```bash
git clone https://github.com/Ron-Zehavi/AlertForge.git
cd AlertForge
./start.sh
```

This creates a virtual environment, installs dependencies, and starts:
- **Backend** (FastAPI) on http://localhost:8000
- **Frontend** (React + Vite) on http://localhost:5173

## Development Commands

```bash
make install     # Install all dependencies
make dev         # Start backend + frontend
make test        # Python tests (85% coverage gate)
make web-test    # Frontend tests
make lint        # Ruff linter
make typecheck   # Mypy strict
make check       # Run all checks
```

## Project Structure

```
alertforge/
├── src/alertforge/
│   ├── api/            # FastAPI app (serve rankings)
│   ├── models/         # Pydantic schemas
│   ├── ranking/        # Ranking model inference
│   ├── features/       # Feature extraction from broker outputs
│   ├── training/       # Model training scripts (not in serving image)
│   └── utils/          # Settings, config
├── web/                # React + Vite frontend
├── infra/              # Terraform (ECR, S3, IAM, dev App Runner)
├── infra/prod/         # Terraform (prod App Runner, separate state)
├── tests/              # pytest
├── configs/            # config.yaml
├── data/               # Raw data, processed data, model artifacts (gitignored)
├── .github/workflows/
│   ├── ci.yml          # Lint + typecheck + test (on PR)
│   └── deploy.yml      # Build + deploy-dev + approval + deploy-prod (on merge)
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## CI/CD Workflow

```
Feature branch → PR → CI checks (lint, typecheck, test)
                       │
                  Merge to main
                       │
              Build Docker image → Push to ECR
                       │
              Auto-deploy to dev
                       │
              Manual approval gate
                       │
              Promote same image to prod
```

- **PR**: CI runs lint, typecheck, and tests on Python 3.11 + 3.12. Blocks merge on failure.
- **Merge to main**: Docker image is built and pushed to ECR with `:sha-<short>` and `:dev` tags.
- **Dev deploy**: Automatic — App Runner pulls the `:dev` image.
- **Prod deploy**: Requires manual approval in GitHub Actions. The exact same image is retagged as `:prod` (no rebuild).

## Infrastructure Setup

Prerequisites: AWS CLI configured with an `alertforge` profile, Terraform >= 1.5.

### 1. GitHub OIDC Provider

If you haven't already set up a GitHub OIDC provider in your AWS account:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --profile alertforge
```

### 2. Shared Infrastructure (ECR, S3, IAM, Dev App Runner)

```bash
cd infra
terraform init
terraform plan
terraform apply
```

Note the outputs — you'll need `github_actions_role_arn`, `dev_service_arn`, and `ecr_repository_url` for GitHub repository variables.

### 3. Production App Runner

```bash
cd infra/prod
terraform init
terraform plan
terraform apply
```

### 4. GitHub Repository Variables

Set these in GitHub → Settings → Environments:

| Variable | Where | Value |
|---|---|---|
| `ROLE_ARN` | Repository variables | `github_actions_role_arn` output |
| `DEV_SERVICE_ARN` | `development` environment | `dev_service_arn` output |
| `PROD_SERVICE_ARN` | `production` environment | `prod_service_arn` output |
| `ECR_REGISTRY` | Repository variables | `ecr_repository_url` (without repo name) |

Set the `production` environment to require reviewer approval (Settings → Environments → production → Required reviewers).

### 5. Push Initial Image

Before the first App Runner deploy, push a seed image:

```bash
aws ecr get-login-password --region us-east-1 --profile alertforge | \
  docker login --username AWS --password-stdin <ECR_REGISTRY>

docker build -t <ECR_REPO_URL>:dev .
docker push <ECR_REPO_URL>:dev
docker tag <ECR_REPO_URL>:dev <ECR_REPO_URL>:prod
docker push <ECR_REPO_URL>:prod
```
