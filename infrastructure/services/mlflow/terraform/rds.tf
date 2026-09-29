resource "random_password" "db" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "mlflow" {
  name       = local.name
  subnet_ids = data.aws_subnets.private.ids

  tags = local.tags
}

resource "aws_db_instance" "mlflow" {
  identifier     = local.name
  engine         = "postgres"
  engine_version = "17"
  instance_class = var.db_instance_class

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "mlflow"
  username = "mlflow"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.mlflow.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period  = 0
  delete_automated_backups = true
  skip_final_snapshot      = true
  deletion_protection      = false
  apply_immediately        = true

  tags = local.tags
}
