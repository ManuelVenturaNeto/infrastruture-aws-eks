variable "vpc_cidr" {
  description = "Bloco CIDR da VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Quantidade de AZs."
  type        = number
  default     = 3
}

variable "single_nat_gateway" {
  description = "true = 1 NAT para todas as AZs."
  type        = bool
  default     = true
}

variable "kubernetes_version" {
  description = "Versao do Kubernetes no EKS."
  type        = string
  default     = "1.34"
}

variable "system_instance_types" {
  description = "Tipos do node group de bootstrap."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "image_repositories" {
  description = "Repositorios ECR criados para as imagens de workload."
  type        = list(string)
  default     = ["spark", "spark-gpu", "spark-rapids"]
}

variable "bastion_instance_type" {
  description = "Tipo da EC2 do bastion de acesso via SSM."
  type        = string
  default     = "t3.micro"
}

variable "bastion_proxy_port" {
  description = "Porta do proxy CONNECT dentro do bastion."
  type        = number
  default     = 3128
}
