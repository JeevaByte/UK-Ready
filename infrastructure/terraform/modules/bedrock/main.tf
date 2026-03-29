# =============================================================================
# AWS Bedrock — model access configuration
# =============================================================================
# Defines the Bedrock model access request for Claude Sonnet.
# Bedrock requires explicit model access to be granted per AWS account.
#
# After deploying this, you must accept the model terms in the AWS console:
# https://eu-west-2.console.aws.amazon.com/bedrock/home#/modelaccess
# =============================================================================

variable "environment" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "eu-west-2"
}

variable "bedrock_model_id" {
  type    = string
  default = "anthropic.claude-sonnet-4-5-20251001"
}

# NOTE: aws_bedrock_model_invocation_logging_configuration is the resource
# to enable Bedrock invocation logging to CloudWatch/S3.
# Model access itself is managed via the AWS console or aws_bedrock_model_access resource.

resource "aws_cloudwatch_log_group" "bedrock_invocations" {
  name              = "/aws/bedrock/invocations/${var.environment}"
  retention_in_days = 30
}

# Bedrock invocation logging — logs all model calls for audit trail
resource "aws_bedrock_model_invocation_logging_configuration" "ukready" {
  logging_config {
    cloudwatch_config {
      log_group_name = aws_cloudwatch_log_group.bedrock_invocations.name
      role_arn       = aws_iam_role.bedrock_logging.arn
    }

    embedding_data_delivery_enabled = false
    image_data_delivery_enabled     = false
    text_data_delivery_enabled      = true
  }
}

# IAM role for Bedrock to write logs to CloudWatch
resource "aws_iam_role" "bedrock_logging" {
  name = "ukready-bedrock-logging-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_logging" {
  name = "ukready-bedrock-logging-policy"
  role = aws_iam_role.bedrock_logging.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.bedrock_invocations.arn}:*"
      }
    ]
  })
}

output "bedrock_log_group_arn" {
  value = aws_cloudwatch_log_group.bedrock_invocations.arn
}
