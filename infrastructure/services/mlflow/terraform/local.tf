locals {
  cluster_name = "${var.name_prefix}-eks"
  name         = "${var.name_prefix}-mlflow"
  namespace    = "mlflow"

  service_accounts = [
    "mlflow",
  ]

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "mlflow"
  }
}
