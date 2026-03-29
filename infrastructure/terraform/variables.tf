# =============================================================================
# UKReady Terraform — Variable Definitions
# =============================================================================

variable "aws_region" {
  description = "AWS region. eu-west-2 (London) for UK data residency."
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "bedrock_model_id" {
  description = "AWS Bedrock model ID to use for inference."
  type        = string
  default     = "anthropic.claude-sonnet-4-5-20251001"
}

# ---------------------------------------------------------------------------
# Feature flags — set to true to deploy each component
# All false by default so nothing is created until explicitly enabled
# ---------------------------------------------------------------------------

variable "deploy_lambda" {
  description = "Set to true to deploy the Lambda + API Gateway backend."
  type        = bool
  default     = false
}

variable "deploy_opensearch" {
  description = "Set to true to deploy OpenSearch Serverless vector store."
  type        = bool
  default     = false
}

variable "deploy_rds" {
  description = "Set to true to deploy RDS Aurora Serverless v2 (PostgreSQL)."
  type        = bool
  default     = false
}
