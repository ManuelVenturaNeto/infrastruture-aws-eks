data "aws_vpc" "cluster" {
  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.cluster.id]
  }

  tags = {
    "karpenter.sh/discovery" = local.cluster_name
  }
}

resource "aws_security_group" "nodes" {
  name        = "${local.name}-nodes"
  description = "Anexado as maquinas do NodePool airflow. Unica origem aceita pelo RDS."
  vpc_id      = data.aws_vpc.cluster.id

  tags = merge(local.tags, { Name = "${local.name}-nodes" })
}

resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "RDS do Airflow. Aceita apenas as maquinas do NodePool airflow."
  vpc_id      = data.aws_vpc.cluster.id

  tags = merge(local.tags, { Name = "${local.name}-db" })
}

resource "aws_vpc_security_group_ingress_rule" "db_from_nodes" {
  security_group_id            = aws_security_group.db.id
  description                  = "Postgres a partir das maquinas do Airflow."
  referenced_security_group_id = aws_security_group.nodes.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}
