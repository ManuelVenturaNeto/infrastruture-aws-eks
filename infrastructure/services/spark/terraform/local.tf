locals {
  cluster_name    = "${var.name_prefix}-eks"
  name            = "${var.name_prefix}-spark"
  lake_bucket_arn = "arn:aws:s3:::${var.name_prefix}-lake"

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "spark"
  }
}
