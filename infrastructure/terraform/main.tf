# =============================================================================
# UKReady — Terraform IaC
# =============================================================================
# Region: eu-west-2 (London) — UK data residency
#
# ALL resources use count = 0 — nothing is deployed yet.
# To deploy a resource, change its count to 1 in terraform.tfvars.
#
# Architecture:
#   Frontend: Vercel (managed separately, not in Terraform)
#   Backend:  AWS Lambda + API Gateway
#   AI:       AWS Bedrock (Claude Sonnet)
#   Vectors:  AWS OpenSearch Serverless
#   Database: AWS RDS Aurora Serverless v2 (PostgreSQL)
#   Storage:  S3 (document store)
#   Logs:     CloudWatch
# =============================================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ukready"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "github.com/jeevabyte/uk-ready"
    }
  }
}

# ---------------------------------------------------------------------------
# IAM Role — Lambda execution role with Bedrock access
# ---------------------------------------------------------------------------
resource "aws_iam_role" "lambda_execution" {
  count = var.deploy_lambda ? 1 : 0

  name = "ukready-lambda-execution-${var.environment}"
  path = "/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  count = var.deploy_lambda ? 1 : 0

  name = "ukready-lambda-bedrock-policy"
  role = aws_iam_role.lambda_execution[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/ukready-*"
      },
      # Bedrock — invoke Claude model only
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.bedrock_model_id}"
      },
      # OpenSearch Serverless
      {
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = "*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# CloudWatch Log Group
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "backend" {
  count = var.deploy_lambda ? 1 : 0

  name              = "/aws/lambda/ukready-backend-${var.environment}"
  retention_in_days = 30
}

# ---------------------------------------------------------------------------
# S3 — Document store (for storing scraped gov.uk content)
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "documents" {
  count = var.deploy_lambda ? 1 : 0

  bucket = "ukready-documents-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "documents" {
  count = var.deploy_lambda ? 1 : 0

  bucket = aws_s3_bucket.documents[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  count = var.deploy_lambda ? 1 : 0

  bucket = aws_s3_bucket.documents[0].id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access — documents are internal only
resource "aws_s3_bucket_public_access_block" "documents" {
  count = var.deploy_lambda ? 1 : 0

  bucket                  = aws_s3_bucket.documents[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# OpenSearch Serverless — vector store for RAG
# (replaces ChromaDB in production for scalability and AWS-native auth)
# ---------------------------------------------------------------------------
module "opensearch" {
  source = "./modules/opensearch"
  count  = var.deploy_opensearch ? 1 : 0

  environment         = var.environment
  aws_region          = var.aws_region
  lambda_role_arn     = var.deploy_lambda ? aws_iam_role.lambda_execution[0].arn : ""
  collection_name     = "ukready-vectors-${var.environment}"
}

# ---------------------------------------------------------------------------
# RDS Aurora Serverless v2 — PostgreSQL
# ---------------------------------------------------------------------------
module "rds" {
  source = "./modules/rds"
  count  = var.deploy_rds ? 1 : 0

  environment = var.environment
  aws_region  = var.aws_region
  db_name     = "ukready"
}

# ---------------------------------------------------------------------------
# Lambda + API Gateway — FastAPI backend
# ---------------------------------------------------------------------------
module "lambda" {
  source = "./modules/lambda"
  count  = var.deploy_lambda ? 1 : 0

  environment        = var.environment
  aws_region         = var.aws_region
  execution_role_arn = aws_iam_role.lambda_execution[0].arn
  bedrock_model_id   = var.bedrock_model_id
  log_group_name     = aws_cloudwatch_log_group.backend[0].name
}

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
data "aws_caller_identity" "current" {}
