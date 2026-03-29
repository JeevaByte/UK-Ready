# =============================================================================
# UKReady Terraform — Outputs
# =============================================================================
# These outputs are used by CI/CD pipelines and for manual reference.
# All outputs are conditional on their feature flag being enabled.
# =============================================================================

output "api_gateway_url" {
  description = "API Gateway URL for the backend (when Lambda is deployed)"
  value       = var.deploy_lambda ? module.lambda[0].api_gateway_url : "Not deployed (deploy_lambda=false)"
}

output "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint (when deployed)"
  value       = var.deploy_opensearch ? module.opensearch[0].collection_endpoint : "Not deployed (deploy_opensearch=false)"
}

output "rds_endpoint" {
  description = "RDS Aurora cluster endpoint (when deployed)"
  value       = var.deploy_rds ? module.rds[0].cluster_endpoint : "Not deployed (deploy_rds=false)"
  sensitive   = true
}

output "documents_s3_bucket" {
  description = "S3 bucket name for document storage (when Lambda is deployed)"
  value       = var.deploy_lambda ? aws_s3_bucket.documents[0].id : "Not deployed (deploy_lambda=false)"
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution IAM role"
  value       = var.deploy_lambda ? aws_iam_role.lambda_execution[0].arn : "Not deployed"
}
