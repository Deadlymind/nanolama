---
name: aws-services
description: Provisions the managed AWS backing services for a Django/DRF app — RDS PostgreSQL, ElastiCache Redis for Celery and Channels, and a private S3 bucket — all locked down with least-privilege security groups, an IAM instance role instead of static keys, and secrets kept in env or Secrets Manager. Use when creating the RDS database, wiring ElastiCache Redis for Celery/Channels, making an S3 bucket, setting security groups, granting the app S3 access, or asking how the AWS data tier is locked down here. Not for the Elastic Beanstalk app tier or Procfile (see deploy-aws) or the GitHub Actions pipeline (see ci-cd).
---

# AWS backing services (private, least-privilege)

## When to use
Standing up or reviewing the managed data tier behind the app: RDS Postgres,
ElastiCache Redis (Celery broker + Channels layer), and an S3 bucket. The
invariant: nothing in this tier is reachable from the public internet, and the
app authenticates to AWS by *role*, never by pasted keys.

## Pattern
Three rules, held for every backing service:

1. **Private by default.** RDS and ElastiCache live in private subnets, are
   *not* publicly accessible, and their security groups allow inbound *only*
   from the app's security group — not `0.0.0.0/0`, not a CIDR.
2. **Role, not keys.** The app reads S3 through an IAM *instance role* attached
   to the compute (EB / EC2). No `AWS_ACCESS_KEY_ID` in code, env, or repo.
3. **S3 is private.** Block Public Access stays ON; objects are served via the
   role + presigned URLs, never a public bucket policy.

## Steps / idioms
The whole tier is one idiom: every data security group takes its source from the
app SG id (never a CIDR), each store stays in a private subnet, and S3 blocks all
public access. One Terraform slice shows all three; ElastiCache and Django wiring
follow the same shape in prose below.

```hcl
# App SG is referenced by every data SG — least privilege is SG-to-SG, not a CIDR.
# Rename "entreprise" to your project throughout.
resource "aws_security_group" "rds" {
  name   = "entreprise-rds"
  vpc_id = var.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]  # SG ref, never 0.0.0.0/0
  }
}
resource "aws_db_instance" "pg" {
  engine                 = "postgres"
  engine_version         = "17"      # pin to the PG major you run (e.g. 16/17/18)
  publicly_accessible    = false     # private subnet only
  db_subnet_group_name   = aws_db_subnet_group.private.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  storage_encrypted      = true
  backup_retention_period = 7        # >0 enables automated backups + PITR; tune the window
  deletion_protection     = true     # a stray `terraform destroy`/console delete is blocked
  # password from Secrets Manager / env — never a literal here
}
resource "aws_s3_bucket_public_access_block" "media" {
  bucket                  = aws_s3_bucket.media.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
# The instance role gets a scoped policy (s3:GetObject/PutObject/DeleteObject on
# this bucket only) — the app never holds an AWS_ACCESS_KEY_ID.
```

**Durable, browser-reachable S3.** Turn on bucket *versioning* so an overwritten
or deleted object can be restored from a prior version — the bucket stays private
throughout. Add a CORS rule whose `AllowedOrigins` is your frontend origin *only*
(e.g. `https://app.example.test`), never `*`, so the browser can load assets via
presigned URLs while Block Public Access stays ON.

**ElastiCache Redis, same posture.** A second SG allows only the app SG on 6379;
that one endpoint backs both the Celery broker/result store and the Channels
layer (`channels_redis.core.RedisChannelLayer`).

**Django reads endpoints from env**, resolved at deploy from Secrets Manager —
e.g. `DATABASE_URL` (parsed with `dj_database_url`), `REDIS_URL` reused for
`CELERY_BROKER_URL` and the channel layer, and `S3_BUCKET`. No credentials in
settings; boto3 picks up the instance role automatically.

## Adapt to your repo
Rename `entreprise-*` resource names, the VPC/subnet ids, the bucket name, and
the region to match your project. Confirm the RDS/ElastiCache SGs reference your
real app SG id (the one on the EB environment) and that `publicly_accessible`
is `false`. Pin `engine_version` to the PG major you run (16/17/18). If you use
CloudFormation/CDK/EB-`.ebextensions` instead of Terraform, the three rules are
identical — only the syntax changes.

## Gotchas
- A data SG whose ingress is a CIDR (`0.0.0.0/0` or an office IP) instead of the
  app SG id is a leak — SG-to-SG rules are the least-privilege form.
- `publicly_accessible = true` on RDS puts the DB on a public IP even inside a
  VPC — keep it `false` and rely on the SG.
- An `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` pair anywhere (env, repo,
  Beanstalk config) means you skipped the instance role — remove it.
- Block Public Access ON can still be undermined by a permissive bucket policy;
  don't add one — serve via presigned URLs from the role.
- ElastiCache Redis has no auth by default; the SG *is* the perimeter, so never
  widen it. Secrets belong in Secrets Manager, injected as env at deploy.
- A DB with `deletion_protection = false` and no backup retention is one typo away
  from unrecoverable loss — automated backups give point-in-time recovery; keep
  both on.
- Keep the app, database, cache, and object storage in the *same* region. A store
  in a different region from the compute is the classic can't-connect bug, adds
  latency, and bills cross-region transfer — confirm the region (keep it a
  variable) before creating each resource.

## See also
- `deploy-aws`
- `ci-cd`
