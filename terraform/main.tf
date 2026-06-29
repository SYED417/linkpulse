# Ask AWS which Availability Zones exist in this region, so we can spread
# our subnets across two of them (required for RDS and for ALB).
data "aws_availability_zones" "available" {
  state = "available"
}

# ---- Networking: VPC, subnets, internet gateway, security groups ----
module "vpc" {
  source              = "./modules/vpc"
  project             = var.project
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  azs                 = slice(data.aws_availability_zones.available.names, 0, 2)
}

# ---- Identity: IAM role + instance profile for the EC2 backend ----
module "iam" {
  source  = "./modules/iam"
  project = var.project
}

# ---- Database: managed PostgreSQL (RDS) ----
module "rds" {
  source               = "./modules/rds"
  project              = var.project
  subnet_ids           = module.vpc.public_subnet_ids
  db_security_group_id = module.vpc.db_sg_id
}

# ---- Container registry: private ECR repo for the backend image ----
resource "aws_ecr_repository" "backend" {
  name         = "${var.project}-backend"
  force_delete = true # allow terraform destroy even if images exist
  tags         = { Name = "${var.project}-backend" }
}

# ---- JWT signing secret (generated, stored encrypted in SSM) ----
resource "random_password" "jwt" {
  length  = 48
  special = false
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/${var.project}/jwt_secret"
  type  = "SecureString"
  value = random_password.jwt.result
  tags  = { Name = "${var.project}-jwt-secret" }
}

# ---- Compute: EC2 instance running the backend container ----
module "ec2" {
  source                = "./modules/ec2"
  project               = var.project
  region                = var.aws_region
  instance_type         = "t3.micro"
  subnet_id             = module.vpc.public_subnet_ids[0]
  security_group_id     = module.vpc.app_sg_id
  instance_profile_name = module.iam.instance_profile_name
  image_uri             = "${aws_ecr_repository.backend.repository_url}:latest"
  ssm_database_url_path = module.rds.ssm_database_url_path
  jwt_ssm_path          = aws_ssm_parameter.jwt_secret.name
}

# ---- Load balancer: public entry point forwarding to the EC2 backend ----
module "alb" {
  source            = "./modules/alb"
  project           = var.project
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.public_subnet_ids
  security_group_id = module.vpc.alb_sg_id
  instance_id       = module.ec2.instance_id
}

# ---- Frontend: S3 bucket + CloudFront CDN (also proxies /api/* to the ALB) ----
module "s3_cdn" {
  source       = "./modules/s3-cdn"
  project      = var.project
  alb_dns_name = module.alb.alb_dns_name
}
