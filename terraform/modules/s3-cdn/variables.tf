variable "project" {
  type = string
}

variable "alb_dns_name" {
  description = "DNS name of the ALB, used as the /api/* origin"
  type        = string
}
