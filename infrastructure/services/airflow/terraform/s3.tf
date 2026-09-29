resource "aws_s3_bucket" "airflow" {
  bucket        = local.name
  force_destroy = true

  tags = local.tags
}
