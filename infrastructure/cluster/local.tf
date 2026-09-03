locals {
  cluster_name = "${var.name_prefix}-eks"

  system_taint_tolerations = [{
    key      = "CriticalAddonsOnly"
    operator = "Exists"
  }]

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "cluster"
  }
}
