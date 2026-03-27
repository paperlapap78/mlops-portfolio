# GitHub OIDC identity provider — one per AWS account.
# If one already exists, import it before applying:
#   terraform import aws_iam_openid_connect_provider.github \
#     arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

locals {
  github_repo = "paperlapap78/mlops-portfolio"
}

data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${local.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "github-actions-mlops-portfolio"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json
}

data "aws_iam_policy_document" "github_actions_ecr_push" {
  # GetAuthorizationToken has no resource-level scope — must target "*"
  statement {
    sid       = "ECRAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "ECRPush"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
    ]
    resources = [aws_ecr_repository.agent_repo.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  name   = "ecr-push"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_ecr_push.json
}

# EKS describe permission — needed by `aws eks update-kubeconfig` in the CD job
data "aws_iam_policy_document" "github_actions_eks" {
  statement {
    sid       = "EKSDescribe"
    actions   = ["eks:DescribeCluster"]
    resources = [aws_eks_cluster.main.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_eks" {
  name   = "eks-describe"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_eks.json
}

# EKS access entry — maps the IAM role to a Kubernetes cluster-admin principal.
# Uses the access entry API (AWS provider >= 5.x) — no aws-auth ConfigMap editing.
resource "aws_eks_access_entry" "github_actions" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.github_actions.arn
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "github_actions_admin" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.github_actions.arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.github_actions]
}

# Local developer access — grants kubectl access for the dev SSO role
resource "aws_eks_access_entry" "developer" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = "arn:aws:iam::339712990928:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_PrincipalDev_9ef405e76c9aa695"
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "developer_admin" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = "arn:aws:iam::339712990928:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_PrincipalDev_9ef405e76c9aa695"
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.developer]
}

output "github_actions_role_arn" {
  description = "Store this as the AWS_ROLE_ARN secret in GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}
