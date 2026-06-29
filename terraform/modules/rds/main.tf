# ---------------------------------------------------------------------------
# 1) Generate a strong random password for the database master user.
#    We never type or hardcode it — Terraform creates it.
#    special = false avoids symbols that would break a connection URL.
# ---------------------------------------------------------------------------
resource "random_password" "db" {
  length  = 20
  special = false
}

# ---------------------------------------------------------------------------
# 2) Store that password in SSM Parameter Store as an encrypted SecureString.
#    This keeps the secret out of git and lets the EC2 server read it later.
# ---------------------------------------------------------------------------
resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project}/db_password"
  type  = "SecureString"
  value = random_password.db.result
  tags  = { Name = "${var.project}-db-password" }
}

# ---------------------------------------------------------------------------
# 3) A DB subnet group: tells RDS which subnets it may place the database in.
#    RDS requires subnets in at least two Availability Zones.
# ---------------------------------------------------------------------------
resource "aws_db_subnet_group" "this" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.subnet_ids
  tags       = { Name = "${var.project}-db-subnet-group" }
}

# ---------------------------------------------------------------------------
# 4) Detect your current public IP (only used when allow_local_access = true)
#    so we can allowlist just your machine to load the schema.
# ---------------------------------------------------------------------------
data "http" "my_ip" {
  url = "https://checkip.amazonaws.com"
}

# Temporary firewall opening: allow Postgres (5432) from YOUR IP only.
# count = 0 disables it entirely when allow_local_access = false.
resource "aws_vpc_security_group_ingress_rule" "local_psql" {
  count             = var.allow_local_access ? 1 : 0
  security_group_id = var.db_security_group_id
  cidr_ipv4         = "${chomp(data.http.my_ip.response_body)}/32"
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
  description       = "Temporary local access to load schema"
}

# ---------------------------------------------------------------------------
# 5) The managed PostgreSQL database itself.
# ---------------------------------------------------------------------------
resource "aws_db_instance" "this" {
  identifier        = "${var.project}-db"
  engine            = "postgres"
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids  = [var.db_security_group_id]

  # When allow_local_access is true, give the DB a public endpoint so your
  # laptop can reach it (still firewalled to your IP + the app SG).
  publicly_accessible = var.allow_local_access

  multi_az            = false  # single-AZ to keep cost down
  skip_final_snapshot = true   # don't create a backup snapshot on destroy
  deletion_protection = false  # allow terraform destroy to remove it

  tags = { Name = "${var.project}-db" }
}

# ---------------------------------------------------------------------------
# 6) Store the FULL connection string (DATABASE_URL) in SSM too. The EC2
#    backend will read this single value in Phase 5C. Built from the live
#    endpoint + the generated password.
# ---------------------------------------------------------------------------
resource "aws_ssm_parameter" "database_url" {
  name  = "/${var.project}/database_url"
  type  = "SecureString"
  value = "postgresql://${var.db_username}:${random_password.db.result}@${aws_db_instance.this.address}:5432/${var.db_name}"
  tags  = { Name = "${var.project}-database-url" }
}
