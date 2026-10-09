terraform {
  required_version = ">= 1.10"

  backend "s3" {
    bucket       = "kube-system-experiment-tfstate"
    key          = "services/airflow/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = local.cluster_name
}
