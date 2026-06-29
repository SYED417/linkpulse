# These values are printed after `terraform apply` and are consumed by the
# next deployment steps (RDS, EC2, ALB).
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "alb_sg_id" {
  value = module.vpc.alb_sg_id
}

output "app_sg_id" {
  value = module.vpc.app_sg_id
}

output "db_sg_id" {
  value = module.vpc.db_sg_id
}

output "ec2_instance_profile" {
  value = module.iam.instance_profile_name
}

# ---- RDS outputs ----
output "db_endpoint" {
  value = module.rds.db_endpoint
}

output "db_name" {
  value = module.rds.db_name
}

output "db_username" {
  value = module.rds.db_username
}

output "ssm_password_path" {
  value = module.rds.ssm_password_path
}

output "ssm_database_url_path" {
  value = module.rds.ssm_database_url_path
}

# ---- ECR / EC2 / ALB outputs ----
output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "ec2_instance_id" {
  value = module.ec2.instance_id
}

output "ec2_public_ip" {
  value = module.ec2.public_ip
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

# ---- S3 + CloudFront outputs ----
output "cloudfront_domain_name" {
  value = module.s3_cdn.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  value = module.s3_cdn.cloudfront_distribution_id
}

output "s3_bucket_name" {
  value = module.s3_cdn.s3_bucket_name
}
