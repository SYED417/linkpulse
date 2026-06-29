variable "project" {
  description = "Name prefix for resources"
  type        = string
}

variable "subnet_ids" {
  description = "Subnets the database may live in (need 2 AZs)"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group that controls access to the database"
  type        = string
}

variable "db_name" {
  description = "Initial database name"
  type        = string
  default     = "linkpulse"
}

variable "db_username" {
  description = "Master username"
  type        = string
  default     = "linkpulse_user"
}

variable "instance_class" {
  description = "RDS instance size"
  type        = string
  default     = "db.t4g.micro"
}

variable "engine_version" {
  description = "PostgreSQL major version"
  type        = string
  default     = "15"
}

variable "allocated_storage" {
  description = "Storage in GB"
  type        = number
  default     = 20
}

variable "allow_local_access" {
  description = "If true, expose the DB to your IP so you can load the schema. Set false to lock it to the app tier."
  type        = bool
  default     = true
}
