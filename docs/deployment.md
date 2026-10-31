# Deployment

## Local demo

Use START.cmd for native SQLite development or `docker compose up --build -d` for PostgreSQL. Neither requires cloud credentials. Docker Desktop must already be running for Compose. Local seed accounts are never appropriate for a public deployment.

## AWS scaffold

The Terraform module describes a VPC, two subnets, HTTPS ALB with API path routing, ECS/Fargate API and web services, private-access RDS PostgreSQL, private encrypted/versioned S3 storage, ECR, Secrets Manager, IAM roles and CloudWatch logs. It is **not deployed automatically**. Cloud services incur charges even if task desired_count is zero (for example ALB/RDS). The initial module is a reviewable portfolio scaffold, not a security or availability certification.

Prerequisites: AWS CLI credentials for your own account, Terraform, Docker, a domain and an issued regional ACM certificate. Use a remote encrypted Terraform backend with locking for shared work. Terraform state contains the database password, even though outputs do not reveal it. Keep state out of Git.

1. Copy `terraform.tfvars.example` to `terraform.tfvars`; set region, domain, certificate ARN and a unique immutable image tag. Keep desired_count=0.
2. Run `terraform init`, `terraform fmt`, `terraform validate`, then review `terraform plan` before applying it yourself.
3. Authenticate Docker to ECR using your AWS CLI, then build/tag/push API and web images to the two repository URLs in Terraform outputs. Example commands below assume you fill in the actual URLs.

```powershell
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.ap-south-1.amazonaws.com
docker build -t <api-repository>:v0.1.0 ./backend
docker build -t <web-repository>:v0.1.0 ./frontend
docker push <api-repository>:v0.1.0
docker push <web-repository>:v0.1.0
```

4. Point your domain to the ALB DNS name. Set desired_count=1, then review and apply another plan. Tasks get public IPs for outbound image/provider access, but task inbound access is restricted to the ALB security group. RDS has no public access and accepts only task security-group traffic. This avoids a NAT gateway in the learning scaffold; a larger deployment can use private task subnets with NAT/VPC endpoints.
5. Register a fresh owner account at your HTTPS domain, create customer/staff accounts and upload knowledge. `SEED_DEMO=false` is fixed in the Terraform API task; production startup rejects demo seeding.
6. Optional: create a provider-key secret yourself and pass its ARN with agent_mode=llm. Never put the key value in Terraform variables or Git.
7. Inspect ECS health and CloudWatch logs. Exercise ticket creation, investigation, restart while paused, approval, rejection and tenant/customer isolation in the actual deployed environment.

Web `/api/*` traffic is routed directly to the API by the ALB. The container's Next rewrite is used by local Compose. API docs are routed to the API as well. Session cookies are Secure in production, and CORS/Origin checks require the configured HTTPS origin.

The MVP has one API task and an in-process worker. Deployment can cause a brief interruption, then persistent workflows recover. Horizontal scaling requires queue/outbox work described in architecture.md. RDS deletion protection and final snapshots are enabled; teardown requires deliberate database settings changes. The document bucket is not force-destroyed. Review retained resources rather than assuming `terraform destroy` removes all data.

## Before a public launch

Implement verified identities/password reset, shared abuse protection, versioned database migrations, billing/quotas if charging customers, operational alerting, data-retention controls and a tested backup/restore procedure. Configure DNS/TLS, secrets and a proper authentication lifecycle. These are remaining engineering tasks, not completed claims.
