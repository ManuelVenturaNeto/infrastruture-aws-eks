module "karpenter" {
  source  = "terraform-aws-modules/eks/aws//modules/karpenter"
  version = "21.25.0"

  cluster_name = module.eks.cluster_name

  namespace       = "kube-system"
  service_account = "karpenter"

  enable_inline_policy     = true
  iam_role_name            = "${var.name_prefix}-karpenter-controller"
  iam_role_use_name_prefix = false

  enable_spot_termination = false

  iam_policy_statements = [{
    sid       = "AllowInterruptionQueueActions"
    resources = [aws_sqs_queue.karpenter.arn]
    actions = [
      "sqs:DeleteMessage",
      "sqs:GetQueueUrl",
      "sqs:ReceiveMessage",
    ]
  }]

  node_iam_role_name            = "${var.name_prefix}-karpenter-node"
  node_iam_role_use_name_prefix = false

  node_iam_role_additional_policies = {
    AmazonSSMManagedInstanceCore = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  }

  tags = local.tags
}

locals {
  karpenter_events = {
    health-event = {
      source      = ["aws.health"]
      detail-type = ["AWS Health Event"]
    }
    spot-interrupt = {
      source      = ["aws.ec2"]
      detail-type = ["EC2 Spot Instance Interruption Warning"]
    }
    instance-rebalance = {
      source      = ["aws.ec2"]
      detail-type = ["EC2 Instance Rebalance Recommendation"]
    }
    instance-state-change = {
      source      = ["aws.ec2"]
      detail-type = ["EC2 Instance State-change Notification"]
    }
    cr-interruption = {
      source      = ["aws.ec2"]
      detail-type = ["EC2 Capacity Reservation Instance Interruption Warning"]
    }
  }
}

resource "aws_sqs_queue" "karpenter" {
  name                      = "${var.name_prefix}-karpenter"
  message_retention_seconds = 300
  sqs_managed_sse_enabled   = true

  tags = local.tags
}

resource "aws_sqs_queue_policy" "karpenter" {
  queue_url = aws_sqs_queue.karpenter.url

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "SqsWrite"
        Effect    = "Allow"
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.karpenter.arn
        Principal = { Service = ["events.amazonaws.com", "sqs.amazonaws.com"] }
      },
      {
        Sid       = "DenyHTTP"
        Effect    = "Deny"
        Action    = "sqs:*"
        Resource  = aws_sqs_queue.karpenter.arn
        Principal = "*"
        Condition = { Bool = { "aws:SecureTransport" = "false" } }
      },
    ]
  })
}

resource "aws_cloudwatch_event_rule" "karpenter" {
  for_each = local.karpenter_events

  name          = "${var.name_prefix}-karpenter-${each.key}"
  event_pattern = jsonencode(each.value)

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "karpenter" {
  for_each = local.karpenter_events

  rule      = aws_cloudwatch_event_rule.karpenter[each.key].name
  target_id = "KarpenterInterruptionQueueTarget"
  arn       = aws_sqs_queue.karpenter.arn
}
