locals {
  pod_identity_trust = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = ["sts:AssumeRole", "sts:TagSession"]
      Principal = { Service = "pods.eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role" "jobs" {
  name               = "${local.name}-jobs"
  assume_role_policy = local.pod_identity_trust

  tags = local.tags
}

resource "aws_iam_role_policy" "jobs_s3" {
  name = "s3"
  role = aws_iam_role.jobs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.spark.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.spark.arn}/*"
      }
    ]
  })
}

resource "aws_eks_pod_identity_association" "jobs" {
  cluster_name    = local.cluster_name
  namespace       = "spark-jobs"
  service_account = "spark"
  role_arn        = aws_iam_role.jobs.arn

  tags = local.tags
}

resource "aws_iam_role" "history" {
  name               = "${local.name}-history"
  assume_role_policy = local.pod_identity_trust

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
        Resource = aws_s3_bucket.spark.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.spark.arn}/*"
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
