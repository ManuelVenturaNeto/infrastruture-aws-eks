resource "aws_s3_bucket" "lake" {
  bucket        = local.name
  force_destroy = true

  tags = local.tags
}
