locals {
  name = "${var.name_prefix}-lake"

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "data"
  }
}
