output "db_endpoint" {
  description = "Hostname of the RDS database"
  value       = aws_db_instance.this.address
}

output "db_name" {
  value = var.db_name
}

output "db_username" {
  value = var.db_username
}

output "ssm_password_path" {
  description = "SSM parameter name holding the DB password"
  value       = aws_ssm_parameter.db_password.name
}

output "ssm_database_url_path" {
  description = "SSM parameter name holding the full DATABASE_URL"
  value       = aws_ssm_parameter.database_url.name
}
