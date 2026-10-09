module "storage" {
  source = "../../../modules/service-storage"

  bucket_name      = local.name
  role_name        = local.name
  cluster_name     = local.cluster_name
  namespace        = local.namespace
  service_accounts = local.service_accounts
  tags             = local.tags
}
