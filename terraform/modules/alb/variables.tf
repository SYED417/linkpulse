variable "project" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  description = "Public subnets for the ALB (need 2 AZs)"
  type        = list(string)
}

variable "security_group_id" {
  description = "ALB security group (open on 80/443)"
  type        = string
}

variable "instance_id" {
  description = "EC2 instance to register as a target"
  type        = string
}
