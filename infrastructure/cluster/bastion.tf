data "aws_ssm_parameter" "bastion_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_iam_role" "bastion" {
  name = "${var.name_prefix}-bastion"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  role       = aws_iam_role.bastion.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bastion" {
  name = "${var.name_prefix}-bastion"
  role = aws_iam_role.bastion.name
}

resource "aws_security_group" "bastion" {
  name        = "${var.name_prefix}-bastion"
  description = "Bastion alcancado apenas por SSM. Sem regra de ingress."
  vpc_id      = module.vpc.vpc_id

  tags = merge(local.tags, { Name = "${var.name_prefix}-bastion" })
}

resource "aws_vpc_security_group_egress_rule" "bastion" {
  security_group_id = aws_security_group.bastion.id
  description       = "Saida para SSM, NAT e a API do EKS."
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "cluster_from_bastion" {
  security_group_id            = module.eks.cluster_security_group_id
  description                  = "Bastion alcanca a API privada do EKS."
  referenced_security_group_id = aws_security_group.bastion.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
}

resource "aws_instance" "bastion" {
  ami                    = data.aws_ssm_parameter.bastion_ami.value
  instance_type          = var.bastion_instance_type
  subnet_id              = module.vpc.private_subnets[0]
  vpc_security_group_ids = [aws_security_group.bastion.id]
  iam_instance_profile   = aws_iam_instance_profile.bastion.name

  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/bastion-user-data.sh", {
    proxy = file("${path.module}/bastion-proxy.py")
    porta = var.bastion_proxy_port
  })

  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(local.tags, { Name = "${var.name_prefix}-bastion" })
}
