# =============================================================================
# RDS Aurora Serverless v2 — PostgreSQL database for production
# =============================================================================
# Serverless v2 scales automatically from 0.5 to 8 ACUs.
# Starts at minimum capacity to keep costs low.
# NOT deployed by default (controlled by deploy_rds flag in root module).
# =============================================================================

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "db_name" {
  type    = string
  default = "ukready"
}

# VPC — use default VPC for simplicity in dev; replace with dedicated VPC in prod
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_db_subnet_group" "ukready" {
  name       = "ukready-${var.environment}"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "ukready-${var.environment}"
  }
}

resource "aws_security_group" "rds" {
  name   = "ukready-rds-${var.environment}"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # Internal traffic only
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_rds_cluster" "ukready" {
  cluster_identifier      = "ukready-${var.environment}"
  engine                  = "aurora-postgresql"
  engine_mode             = "provisioned"
  engine_version          = "16.2"
  database_name           = var.db_name
  master_username         = "ukready_admin"
  manage_master_user_password = true  # Stored in Secrets Manager
  db_subnet_group_name    = aws_db_subnet_group.ukready.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  deletion_protection     = var.environment == "prod"
  skip_final_snapshot     = var.environment != "prod"
  storage_encrypted       = true

  serverlessv2_scaling_configuration {
    min_capacity = 0.5  # Scale to zero when idle
    max_capacity = 8.0
  }
}

resource "aws_rds_cluster_instance" "ukready" {
  cluster_identifier = aws_rds_cluster.ukready.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.ukready.engine
  engine_version     = aws_rds_cluster.ukready.engine_version
}

output "cluster_endpoint" {
  value     = aws_rds_cluster.ukready.endpoint
  sensitive = true
}

output "cluster_identifier" {
  value = aws_rds_cluster.ukready.cluster_identifier
}
