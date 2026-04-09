terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

variable "aws_region" {
  default = "us-east-1"
}

variable "aws_profile" {
  default = "alertforge"
}

variable "project" {
  default = "alertforge"
}

variable "container_port" {
  default = 8000
}

# Reference shared resources
data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "app" {
  name = var.project
}

data "aws_iam_role" "apprunner_ecr" {
  name = "${var.project}-apprunner-ecr"
}

# Production App Runner
resource "aws_apprunner_service" "prod" {
  service_name = "${var.project}-prod"

  source_configuration {
    authentication_configuration {
      access_role_arn = data.aws_iam_role.apprunner_ecr.arn
    }

    image_repository {
      image_identifier      = "${data.aws_ecr_repository.app.repository_url}:prod"
      image_repository_type = "ECR"

      image_configuration {
        port = tostring(var.container_port)
      }
    }

    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/api/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }
}

output "prod_url" {
  value = "https://${aws_apprunner_service.prod.service_url}"
}

output "prod_service_arn" {
  value = aws_apprunner_service.prod.arn
}
