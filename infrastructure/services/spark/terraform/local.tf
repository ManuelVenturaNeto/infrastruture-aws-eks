locals {
  cluster_name = "${var.name_prefix}-eks"
  name         = "${var.name_prefix}-spark"

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "spark"
  }
}
