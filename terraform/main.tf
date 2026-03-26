# Amazon ECR Repository (Registry)
resource "aws_ecr_repository" "agent_repo" {
  name                 = "ai-agent-repository"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Delete repo even if it contains images — ensures clean terraform destroy

  image_scanning_configuration {
    scan_on_push = true
  }
}

# AWS Secrets Manager (for AI API Keys)
resource "aws_secretsmanager_secret" "ai_secrets" {
  name = "ai-agent-secrets-${var.environment}"
  recovery_window_in_days = 0 # Forces immediate deletion if destroyed to save costs
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = module.vpc.private_subnets
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]
}

# Managed Node Group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "default-node-group"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = module.vpc.private_subnets

  scaling_config {
    desired_size = 1
    max_size     = 2
    min_size     = 1
  }

  instance_types = ["t3.medium"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_worker_policy,
    aws_iam_role_policy_attachment.eks_node_cni_policy,
    aws_iam_role_policy_attachment.eks_node_ecr_policy,
  ]
}

# CloudWatch Logs for Observability
resource "aws_cloudwatch_log_group" "eks_logs" {
  name              = "/aws/eks/${var.cluster_name}/logs"
  retention_in_days = 1    # Minimise log storage cost — logs expire after 1 day
  skip_destroy      = false # Explicitly delete this log group on terraform destroy (default is false, but stated clearly)
}

# Outputs — printed after terraform apply; used to populate .env for local development
output "opensearch_endpoint" {
  description = "OpenSearch Serverless collection endpoint — paste into OPENSEARCH_ENDPOINT in .env"
  value       = aws_opensearchserverless_collection.agent_collection.collection_endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL — used when building and pushing the Docker image"
  value       = aws_ecr_repository.agent_repo.repository_url
}
