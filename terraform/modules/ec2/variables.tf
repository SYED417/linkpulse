variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "subnet_id" {
  description = "Public subnet to launch the instance in"
  type        = string
}

variable "security_group_id" {
  description = "App security group (allows 8000 from the ALB)"
  type        = string
}

variable "instance_profile_name" {
  description = "IAM instance profile granting SSM + ECR access"
  type        = string
}

variable "image_uri" {
  description = "Full ECR image URI to run, including :tag"
  type        = string
}

variable "ssm_database_url_path" {
  description = "SSM parameter name holding the DATABASE_URL"
  type        = string
}

variable "jwt_ssm_path" {
  description = "SSM parameter name holding the JWT signing secret"
  type        = string
}
