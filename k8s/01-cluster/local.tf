locals {
  cluster_name = "${var.name_prefix}-eks"

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "cluster"
  }
}
