module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.25.0"

  name               = local.cluster_name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_cluster_creator_admin_permissions = true

  endpoint_private_access = true
  endpoint_public_access  = false

  encryption_config = null

  create_cloudwatch_log_group            = true
  cloudwatch_log_group_retention_in_days = 7
  enabled_log_types                      = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  node_security_group_tags = {
    "karpenter.sh/discovery" = local.cluster_name
  }

  eks_managed_node_groups = {
    system = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.system_instance_types

      min_size     = 2
      max_size     = 3
      desired_size = 2

      labels = {
        role = "system"
      }

      taints = {
        addons = {
          key    = "CriticalAddonsOnly"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }

  addons = {
    "vpc-cni" = {
      before_compute              = true
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"

      configuration_values = jsonencode({
        env = {
          ENABLE_PREFIX_DELEGATION = "true"
          WARM_PREFIX_TARGET       = "1"
        }
      })
    }

    "kube-proxy" = {
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"
    }

    "coredns" = {
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"

      configuration_values = jsonencode({
        tolerations = local.system_taint_tolerations
      })
    }

    "eks-pod-identity-agent" = {
      before_compute              = true
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"
    }

    "aws-ebs-csi-driver" = {
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"

      configuration_values = jsonencode({
        controller = {
          tolerations = local.system_taint_tolerations
        }
      })

      pod_identity_association = [{
        role_arn        = module.ebs_csi_pod_identity.iam_role_arn
        service_account = "ebs-csi-controller-sa"
      }]
    }

    "metrics-server" = {
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"

      configuration_values = jsonencode({
        tolerations = local.system_taint_tolerations
      })
    }

    "snapshot-controller" = {
      resolve_conflicts_on_create = "OVERWRITE"
      resolve_conflicts_on_update = "OVERWRITE"

      configuration_values = jsonencode({
        tolerations = local.system_taint_tolerations
      })
    }
  }

  tags = local.tags
}

module "ebs_csi_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "2.9.0"

  name                      = "${var.name_prefix}-ebs-csi"
  attach_aws_ebs_csi_policy = true

  tags = local.tags
}
