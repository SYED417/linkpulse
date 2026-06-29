variable "project" {
  description = "Name prefix for resources"
  type        = string
}

variable "vpc_cidr" {
  description = "IP range for the VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "IP ranges for the public subnets"
  type        = list(string)
}

variable "azs" {
  description = "Availability Zones to place subnets in"
  type        = list(string)
}
