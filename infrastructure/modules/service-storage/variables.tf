variable "bucket_name" {
  description = "Name of the service S3 bucket."
  type        = string
}

variable "role_name" {
  description = "Name of the IAM role with read and write access to the bucket."
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster where the role is associated with the service accounts."
  type        = string
}

variable "namespace" {
  description = "Namespace of the service accounts that assume the role."
  type        = string
}

variable "service_accounts" {
  description = "Service accounts that receive the role through Pod Identity."
  type        = list(string)
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
}
