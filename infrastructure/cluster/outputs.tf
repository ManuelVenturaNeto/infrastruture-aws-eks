output "cluster_name" {
  description = "Nome do cluster EKS."
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint da API do EKS."
  value       = module.eks.cluster_endpoint
}

output "karpenter_node_iam_role_name" {
  description = "Role usada no spec.role do EC2NodeClass."
  value       = module.karpenter.node_iam_role_name
}

output "karpenter_queue_name" {
  description = "Fila SQS de interrupcao de spot."
  value       = module.karpenter.queue_name
}

output "azs" {
  description = "AZs em uso. Se vierem menos de 3, reveja a regiao antes do Kafka."
  value       = local.azs
}

output "configure_kubectl" {
  description = "Comando para gerar o kubeconfig."
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}

output "region" {
  description = "Regiao AWS do stack."
  value       = var.region
}

output "ecr_registry" {
  description = "Host do registry ECR, usado no docker login e no build das imagens."
  value       = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"
}

output "ecr_repository_urls" {
  description = "URL de cada repositorio ECR criado."
  value       = { for name, repo in aws_ecr_repository.images : name => repo.repository_url }
}

output "bastion_instance_id" {
  description = "Instancia usada pelo tunnel.sh para alcancar a API privada do EKS."
  value       = aws_instance.bastion.id
}
