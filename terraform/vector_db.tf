# Amazon OpenSearch Serverless (Vector Database)

resource "aws_opensearchserverless_collection" "agent_collection" {
  name        = "ai-agent-collection"
  type        = "VECTORSEARCH"
  description = "Vector database for the AI Agent RAG pipeline"

  # Security and encryption policies MUST exist before the collection
  depends_on = [
    aws_opensearchserverless_security_policy.agent_security,
    aws_opensearchserverless_security_policy.agent_encryption
  ]
}

# Access Policy (Essential for actually using the collection)
resource "aws_opensearchserverless_access_policy" "agent_access" {
  name        = "ai-agent-access-policy"
  type        = "data"
  description = "Allow EKS nodes to access the vector database"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource     = ["collection/${aws_opensearchserverless_collection.agent_collection.name}"],
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index",
          Resource     = ["index/${aws_opensearchserverless_collection.agent_collection.name}/*"],
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ],
      Principal = [
        aws_iam_role.eks_node_role.arn
      ]
    }
  ])
}

# Security Policy (Encryption and Network)
resource "aws_opensearchserverless_security_policy" "agent_security" {
  name        = "ai-agent-security-policy"
  type        = "network"
  description = "Public access for the vector database (for development simplicity)"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection",
          Resource     = ["collection/ai-agent-collection"]
        }
      ],
      AllowFromPublic = true
    }
  ])
}

resource "aws_opensearchserverless_security_policy" "agent_encryption" {
  name        = "ai-agent-encryption-policy"
  type        = "encryption"
  description = "Encryption policy for the vector database"
  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection",
        Resource     = ["collection/ai-agent-collection"]
      }
    ],
    AWSOwnedKey = true
  })
}
