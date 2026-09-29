resource "aws_s3_bucket" "mlflow" {
  bucket        = local.name
  force_destroy = true

  tags = local.tags
}
