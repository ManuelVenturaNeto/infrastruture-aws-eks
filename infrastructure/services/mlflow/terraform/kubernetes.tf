resource "kubernetes_secret_v1" "db" {
  metadata {
    name      = "mlflow-db"
    namespace = local.namespace
  }

  data = {
    username = aws_db_instance.mlflow.username
    password = random_password.db.result
  }
}

resource "kubernetes_service_v1" "db" {
  metadata {
    name      = "mlflow-db"
    namespace = local.namespace
  }

  spec {
    type          = "ExternalName"
    external_name = aws_db_instance.mlflow.address
  }
}
