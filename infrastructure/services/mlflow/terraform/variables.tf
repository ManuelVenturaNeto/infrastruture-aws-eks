variable "db_instance_class" {
  description = "Classe da instancia RDS do backend store."
  type        = string
  default     = "db.t4g.micro"
}
