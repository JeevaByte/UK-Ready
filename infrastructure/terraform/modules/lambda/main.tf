# =============================================================================
# Lambda + API Gateway — FastAPI backend for production
# =============================================================================
# Uses Mangum to wrap FastAPI as a Lambda handler.
# API Gateway v2 (HTTP API) is cheaper and lower latency than REST API.
# NOT deployed by default (controlled by deploy_lambda flag in root module).
# =============================================================================

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "execution_role_arn" {
  type        = string
  description = "IAM role ARN for Lambda execution"
}

variable "bedrock_model_id" {
  type = string
}

variable "log_group_name" {
  type = string
}

# Lambda function
# NOTE: The actual deployment package (ZIP with the FastAPI app + Mangum wrapper)
# is built and uploaded by the CI/CD pipeline. The filename is a placeholder.
resource "aws_lambda_function" "backend" {
  function_name = "ukready-backend-${var.environment}"
  role          = var.execution_role_arn
  runtime       = "python3.11"
  handler       = "mangum_handler.handler"
  timeout       = 30  # 30s — RAG + LLM call needs time
  memory_size   = 1024  # 1GB — sentence-transformers benefit from more memory

  # Placeholder — replaced with real ZIP by CI/CD
  filename         = "/dev/null"
  source_code_hash = filebase64sha256("/dev/null")

  environment {
    variables = {
      AI_PROVIDER      = "bedrock"
      BEDROCK_MODEL_ID = var.bedrock_model_id
      AWS_REGION       = var.aws_region
      ENVIRONMENT      = var.environment
      LOG_LEVEL        = "INFO"
      # DATABASE_URL and CHROMA_HOST injected from Secrets Manager at deploy time
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = var.log_group_name
  }
}

# API Gateway HTTP API (v2) — cheaper + lower latency than REST API
resource "aws_apigatewayv2_api" "backend" {
  name          = "ukready-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.environment == "prod" ? ["https://ukready.app"] : ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.backend.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = "arn:aws:logs:${var.aws_region}:*:log-group:${var.log_group_name}"
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*/*"
}

output "api_gateway_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "lambda_function_name" {
  value = aws_lambda_function.backend.function_name
}
