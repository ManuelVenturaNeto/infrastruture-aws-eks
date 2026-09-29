locals {
  cluster_name = "${var.name_prefix}-eks"
  name         = "${var.name_prefix}-airflow"
  namespace    = "airflow"

  service_accounts = [
    "airflow-api-server",
    "airflow-dag-processor",
    "airflow-scheduler",
    "airflow-triggerer",
    "airflow-worker",
  ]

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
    Layer     = "airflow"
  }
}
