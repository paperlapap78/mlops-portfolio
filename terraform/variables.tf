variable "aws_region" {
  description = "Target AWS Region for deployment"
  default     = "eu-central-1"
}

variable "environment" {
  description = "Differentiator for the workspace (e.g. dev, training, prod)"
  default     = "dev"
}

variable "cluster_name" {
  description = "Name for the EKS Cluster"
  default     = "ai-agent-eks"
}
