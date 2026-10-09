module "storage" {
  source = "../../../modules/service-storage"

  bucket_name      = local.name
  role_name        = "${local.name}-jobs"
  cluster_name     = local.cluster_name
  namespace        = "spark-jobs"
  service_accounts = ["spark"]
  tags             = local.tags
}

resource "aws_s3_object" "event_logs" {
  bucket  = module.storage.bucket_id
  key     = "event-logs/"
  content = ""
}
