terraform {
  required_version = ">= 1.10"

  backend "s3" {
    bucket       = "kube-system-experiment-tfstate"
    key          = "cluster/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}
