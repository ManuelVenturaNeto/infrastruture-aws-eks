resource "aws_iam_role_policy" "jobs_lake" {
  name = "lake"
  role = module.storage.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = local.lake_bucket_arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${local.lake_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role" "history" {
  name = "${local.name}-history"

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

resource "aws_iam_role_policy" "history_s3" {
  name = "s3"
  role = aws_iam_role.history.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = module.storage.bucket_arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${module.storage.bucket_arn}/*"
      }
    ]
  })
}

resource "aws_eks_pod_identity_association" "history" {
  cluster_name    = local.cluster_name
  namespace       = "spark-history"
  service_account = "spark-history"
  role_arn        = aws_iam_role.history.arn

  tags = local.tags
}
