resource "aws_s3_bucket" "spark" {
  bucket        = local.name
  force_destroy = true

  tags = local.tags
}

resource "aws_s3_object" "event_logs" {
  bucket  = aws_s3_bucket.spark.id
  key     = "event-logs/"
  content = ""
}
