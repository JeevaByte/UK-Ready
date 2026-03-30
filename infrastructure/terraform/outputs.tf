# =============================================================================
# UKReady Terraform — Outputs
# =============================================================================
# Uses try() to safely reference count-indexed module outputs.
# When a module has count=0 (not deployed), try() returns the fallback string
# instead of causing a "Invalid index" error during terraform validate/plan.
# =============================================================================

output "api_gateway_url" {
  description = "API Gateway URL for the backend (when Lambda is deployed)"
  value       = try(module.lambda[0].api_gateway_url, "Not deployed — set deploy_lambda=true")
}

output "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint (when deployed)"
  value       = try(module.opensearch[0].collection_endpoint, "Not deployed — set deploy_opensearch=true")
}

output "rds_endpoint" {
  description = "RDS Aurora cluster endpoint (when deployed)"
  value       = try(module.rds[0].cluster_endpoint, "Not deployed — set deploy_rds=true")
  sensitive   = true
}

output "documents_s3_bucket" {
  description = "S3 bucket name for document storage (when Lambda is deployed)"
  value       = try(aws_s3_bucket.documents[0].id, "Not deployed — set deploy_lambda=true")
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution IAM role"
  value       = try(aws_iam_role.lambda_execution[0].arn, "Not deployed — set deploy_lambda=true")
}
