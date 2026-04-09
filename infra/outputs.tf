output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "s3_bucket" {
  value = aws_s3_bucket.data.id
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}
