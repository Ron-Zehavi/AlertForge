resource "aws_apprunner_service" "dev" {
  service_name = "${var.project}-dev"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.app.repository_url}:dev"
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

output "dev_url" {
  value = "https://${aws_apprunner_service.dev.service_url}"
}

output "dev_service_arn" {
  value = aws_apprunner_service.dev.arn
}
