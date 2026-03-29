# =============================================================================
# UKReady — Dev Environment Terraform Variables
# =============================================================================
# All deploy_* flags are false — nothing is created until you explicitly
# enable each component and run `terraform apply`.
#
# To deploy: change a flag to true, run `terraform plan`, then `terraform apply`.
# =============================================================================

aws_region   = "eu-west-2"
environment  = "dev"

bedrock_model_id = "anthropic.claude-sonnet-4-5-20251001"

# Deploy nothing by default — local Docker Compose is used for development
deploy_lambda     = false
deploy_opensearch = false
deploy_rds        = false
