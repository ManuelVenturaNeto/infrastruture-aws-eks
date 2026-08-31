variable "region" {
  description = "Regiao AWS onde o stack e criado."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefixo aplicado ao nome de todos os recursos."
  type        = string
  default     = "kube-system-experiment"
}
