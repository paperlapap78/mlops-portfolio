# Fetch available Availability Zones for the specified region
data "aws_availability_zones" "available" {}

# Using the official AWS VPC module heavily accelerates network creation securely
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ai-agent-vpc-${var.environment}"
  cidr = "10.0.0.0/16"

  # EKS strictly requires at least 2 availability zones
  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  
  # Private subnets are where the actual EKS nodes (t3.medium) will live 
  # so they cannot be reached from the public internet directly.
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  
  # Public subnets hold the NAT Gateway and Load Balancers
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # NAT Gateway is mandatory for private subnet instances to reach out 
  # to the internet (e.g. to download Docker images or contact Bedrock API).
  enable_nat_gateway = true
  single_nat_gateway = true # Sets up just one NAT to save a lot of money on dev environments

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = var.environment
    Project     = "AI-Agent"
  }
}
