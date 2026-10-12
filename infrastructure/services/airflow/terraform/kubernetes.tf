data "aws_caller_identity" "current" {}

resource "kubernetes_config_map_v1" "spark" {
  metadata {
    name      = "airflow-spark"
    namespace = local.namespace
  }

  data = {
    ECR_REGISTRY = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
  }
}

resource "random_password" "api_secret_key" {
  length  = 32
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 32
  special = false
}

resource "kubernetes_secret_v1" "metadata" {
  metadata {
    name      = "airflow-metadata"
    namespace = local.namespace
  }

  data = {
    connection = "postgresql://${aws_db_instance.airflow.username}:${random_password.db.result}@${aws_db_instance.airflow.address}:5432/${aws_db_instance.airflow.db_name}?sslmode=require"
  }
}

resource "kubernetes_secret_v1" "fernet_key" {
  metadata {
    name      = "airflow-fernet-key"
    namespace = local.namespace
  }

  data = {
    "fernet-key" = replace(replace(base64sha256("${local.name}-fernet-key"), "+", "-"), "/", "_")
  }
}

resource "kubernetes_secret_v1" "api_secret_key" {
  metadata {
    name      = "airflow-api-secret-key"
    namespace = local.namespace
  }

  data = {
    "api-secret-key" = random_password.api_secret_key.result
  }
}

resource "kubernetes_secret_v1" "jwt_secret" {
  metadata {
    name      = "airflow-jwt-secret"
    namespace = local.namespace
  }

  data = {
    "jwt-secret" = random_password.jwt_secret.result
  }
}
