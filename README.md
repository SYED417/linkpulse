# LinkPulse

A cloud-native URL shortener and click-analytics platform — built with FastAPI, React, Docker, and deployed to AWS entirely through Terraform.

![Deploy](https://github.com/SYED417/linkpulse/actions/workflows/deploy.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC)

> Live demo: `https://d2c07uke5z7e5.cloudfront.net` (available during demos; tear down with `terraform destroy` to avoid cost)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + Vite (SPA), React Router, Recharts |
| Backend | FastAPI (Python 3.11), SQLAlchemy |
| Database | PostgreSQL 15 (Amazon RDS) |
| Containerization | Docker, docker-compose (local) |
| Registry | Amazon ECR |
| Compute | Amazon EC2 (Amazon Linux 2023) |
| Load balancing | Application Load Balancer (ALB) |
| CDN / hosting | Amazon S3 + CloudFront |
| Secrets | AWS SSM Parameter Store |
| Infra as Code | Terraform |
| CI/CD | GitHub Actions |
| Load testing | k6 |

---

## How It Works

1. A user submits a long URL through the React frontend.
2. The FastAPI backend generates a unique short code and stores the link in PostgreSQL.
3. Visiting `/{short_code}` returns a 307 redirect to the original URL and records a click — capturing IP, referrer, **device type** (from the User-Agent) and **country** (best-effort GeoIP from the real client IP).
4. The analytics endpoint aggregates clicks per link: totals, today, top referrers, a 7-day trend, and breakdowns by device and country.

### Frontend pages
A React Router single-page app with three pages:
- **Create** — form to shorten a URL (scheme optional; `https://` is added automatically).
- **My Links** — table of all links, each linking out to its short URL and to its analytics.
- **Analytics** — charts (Recharts): clicks-over-time line chart, device pie chart, country bar chart, plus top referrers.

### API routes
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/health` | Liveness check |
| POST | `/api/links` | Create a short link |
| GET | `/api/links` | List links |
| GET | `/api/users` | List users |
| GET | `/{short_code}` | Redirect + record click |
| GET | `/api/analytics/{short_code}` | Click analytics |

---

## AWS Architecture

```
                          ┌─────────────────────────────┐
   Browser ──HTTPS──────► │        CloudFront (CDN)     │
                          │  ┌───────────┬────────────┐ │
                          │  │ default → │ /api/* →    │ │
                          │  │   S3      │   ALB       │ │
                          └──┴─────┬─────┴──────┬──────┘ │
                                   │            │
                         ┌─────────▼──┐   ┌─────▼───────────┐
                         │ S3 (React) │   │ ALB (public)    │
                         └────────────┘   └─────┬───────────┘
                                                │
                                        ┌───────▼─────────┐
                                        │ EC2 + Docker    │
                                        │ (FastAPI)       │
                                        └───────┬─────────┘
                                                │
                                        ┌───────▼─────────┐
                                        │ RDS PostgreSQL  │
                                        └─────────────────┘

Secrets in SSM Parameter Store · Image in ECR · All provisioned by Terraform
```

- **Network**: custom VPC, 2 public subnets across 2 AZs, internet gateway, route tables.
- **Security**: three chained security groups — internet→ALB (80/443), ALB→app (8000), app→DB (5432). The database is reachable only from the app tier.
- **Secrets**: the DB password and connection string live encrypted in SSM; the EC2 instance reads them at runtime via its IAM role. Nothing sensitive is in the code or git.

---

## Deploy

Prerequisites: AWS CLI (configured), Terraform, Docker.

```bash
# 1. Provision networking + IAM
cd terraform
terraform init

# 2. Create the ECR repo first, then push the backend image
terraform apply -target=aws_ecr_repository.backend
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t <account>.dkr.ecr.us-east-1.amazonaws.com/linkpulse-backend:latest ../backend
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/linkpulse-backend:latest

# 3. Provision everything else (RDS, EC2, ALB, S3, CloudFront)
terraform apply

# 4. Build & upload the frontend
cd ../frontend
npm ci && npm run build
aws s3 sync dist "s3://$(terraform -chdir=../terraform output -raw s3_bucket_name)" --delete
aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
```

### Tear down (stop all billing)
```bash
cd terraform
terraform destroy
```

---

## CI/CD

`.github/workflows/deploy.yml` runs on every push to `main`:
- **Backend**: build image → push to ECR → redeploy on EC2 via AWS SSM (no SSH).
- **Frontend**: build → `s3 sync` → CloudFront invalidation.

Secrets are stored in GitHub repository secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `EC2_INSTANCE_ID`, `S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`).

---

## Load Test Results

Tested with k6 — 50 virtual users for 30 seconds against the redirect endpoint:

| Metric | Result |
|--------|--------|
| Total requests | 4,933 (~163 req/s) |
| Success rate | 99.98% |
| Avg latency | 303 ms |
| p95 latency | 433 ms |
| Click rows written to RDS | 4,932 (zero data loss) |
| EC2 CPU under load | ~20% (t3.micro) |

Run it yourself: `k6 run loadtest.js`

---

## Testing

The backend has an automated test suite (`backend/tests/`) using `pytest` and FastAPI's `TestClient`, run against a real PostgreSQL instance:

```bash
cd backend
pip install -r requirements-dev.txt
# point at a local test DB, then:
pytest -q
```

Coverage includes the health check, link creation (including 404 for unknown users and 422 for invalid URLs), the redirect + click-recording flow, and analytics. **CI runs these tests on every push and blocks deployment if any fail** (the `test` job is a required dependency of both deploy jobs).

---

## Design Decisions & Trade-offs

- **UUID primary keys** instead of auto-increment integers — non-guessable, no enumeration of how many links/users exist, and safe for distributed inserts.
- **307 (temporary) redirects, not 301** — a 301 is cached by browsers, which would skip the server and lose click analytics. 307 guarantees every click is counted.
- **Save the click before redirecting** — once the redirect response is sent the request is over, so the click is persisted first to guarantee analytics integrity.
- **ECR over Docker Hub** — keeps the image private, authenticates via the existing AWS credentials (no extra account), and keeps the whole system in one cloud.
- **CloudFront proxies `/api/*` to the ALB** — serves frontend and API from one HTTPS domain, which avoids mixed-content errors and removes the need for CORS in production.
- **Secrets in SSM Parameter Store** — the DB password and connection string are encrypted at rest and injected into the container at boot via the instance's IAM role; nothing sensitive touches the code or git.
- **Single EC2 + ALB instead of ECS/EKS** — deliberately the smallest production-style footprint for the use case; ECS Fargate is the documented next step.
- **Chained security groups** — each tier only accepts traffic from the tier in front (internet→ALB→app→DB), so the database is never reachable from the internet.

## Security

- DB password and `DATABASE_URL` live only in encrypted SSM parameters and GitHub Secrets — never in code or version control.
- `.gitignore` excludes `.env`, Terraform state (which contains secrets), and credentials.
- The database is in private security-group isolation, reachable only from the application tier.
- Server management uses AWS SSM Session Manager — **no SSH port is open**.
- The backend safely discards non-IP client values before writing to the database.

## What I'd Build Next

- Migrate compute from EC2 to **ECS Fargate** (no servers to patch, autoscaling).
- **HTTPS on a custom domain** via ACM + Route 53.
- **Authentication** (currently the API trusts a user id) — JWT or Cognito.
- Enrich analytics further: swap the best-effort GeoIP API for a local **MaxMind** database or the `CloudFront-Viewer-Country` header (device + country capture is already implemented).
- **Remote Terraform state** (S3 + DynamoDB lock) and **GitHub OIDC** instead of long-lived AWS keys.
- Read the real client IP from `X-Forwarded-For` behind the ALB.

---

## Architecture Diagram (Excalidraw)

Recreate the diagram at [excalidraw.com](https://excalidraw.com):
1. Draw a **Browser** box at the top.
2. Arrow down to a **CloudFront** box; inside note two paths: `default → S3` and `/api/* → ALB`.
3. Branch to an **S3 (React frontend)** box and an **ALB** box.
4. From ALB, arrow to **EC2 (Docker / FastAPI)**, then to **RDS PostgreSQL**.
5. Add side notes: **SSM Parameter Store** (secrets), **ECR** (image), **Terraform** (provisions all).
6. Label arrows with protocols (HTTPS to CloudFront, HTTP internally) and ports (443, 8000, 5432).
7. Export as PNG and drop it into this README under the Architecture section.

---

## Local Development

```bash
# Backend + DB via Docker
docker compose up --build
# Frontend
cd frontend && npm install && npm run dev
```
