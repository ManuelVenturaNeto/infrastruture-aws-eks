resource "aws_iam_role" "mlflow" {
  name = local.name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = ["sts:AssumeRole", "sts:TagSession"]
      Principal = { Service = "pods.eks.amazonaws.com" }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "mlflow_s3" {
  name = "s3"
  role = aws_iam_role.mlflow.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.mlflow.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.mlflow.arn}/*"
      }
    ]
  })
}

resource "aws_eks_pod_identity_association" "mlflow" {
  for_each = toset(local.service_accounts)

  cluster_name    = local.cluster_name
  namespace       = local.namespace
  service_account = each.value
  role_arn        = aws_iam_role.mlflow.arn

  tags = local.tags
}
