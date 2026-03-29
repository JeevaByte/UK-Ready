# =============================================================================
# OpenSearch Serverless — vector store for production RAG
# =============================================================================
# Replaces ChromaDB (local dev) with AWS-managed, scalable vector search.
# NOT deployed by default (controlled by deploy_opensearch flag in root module).
# =============================================================================

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "lambda_role_arn" {
  type        = string
  description = "ARN of the Lambda execution role to grant data access"
}

variable "collection_name" {
  type = string
}

# Encryption policy
resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "ukready-encryption-${var.environment}"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.collection_name}"]
      }
    ]
    AWSOwnedKey = true
  })
}

# Network policy — private access (no public endpoint)
resource "aws_opensearchserverless_security_policy" "network" {
  name = "ukready-network-${var.environment}"
  type = "network"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${var.collection_name}"]
        },
        {
          ResourceType = "dashboard"
          Resource     = ["collection/${var.collection_name}"]
        }
      ]
      AllowFromPublic = false
    }
  ])
}

# Data access policy — Lambda role can read/write
resource "aws_opensearchserverless_access_policy" "data" {
  name = "ukready-data-${var.environment}"
  type = "data"

  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "index"
          Resource     = ["index/${var.collection_name}/*"]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        },
        {
          ResourceType = "collection"
          Resource     = ["collection/${var.collection_name}"]
          Permission   = ["aoss:CreateCollectionItems", "aoss:DescribeCollectionItems"]
        }
      ]
      Principal = [var.lambda_role_arn]
    }
  ])
}

# The collection itself
resource "aws_opensearchserverless_collection" "vectors" {
  name = var.collection_name
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_access_policy.data,
  ]
}

output "collection_endpoint" {
  value = aws_opensearchserverless_collection.vectors.collection_endpoint
}

output "collection_id" {
  value = aws_opensearchserverless_collection.vectors.id
}
