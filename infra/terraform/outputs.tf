output "alb_dns_name" { value = aws_lb.main.dns_name }
output "ecr_repositories" { value = { for key, repo in aws_ecr_repository.app : key => repo.repository_url } }
output "document_bucket" { value = aws_s3_bucket.documents.id }
output "cluster_name" { value = aws_ecs_cluster.main.name }
output "log_group" { value = aws_cloudwatch_log_group.app.name }
