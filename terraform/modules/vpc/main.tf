# ---------------- VPC ----------------
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.project}-vpc" }
}

# Internet Gateway: lets resources in public subnets reach the internet.
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.project}-igw" }
}

# Two public subnets, one in each Availability Zone.
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project}-public-${count.index + 1}" }
}

# Route table that sends all outbound traffic to the internet gateway.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
  tags = { Name = "${var.project}-public-rt" }
}

# Attach that route table to both public subnets.
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ---------------- Security Groups ----------------
# A security group is a virtual firewall. We chain them so each tier only
# accepts traffic from the tier in front of it.

# 1) ALB: open to the internet on 80/443.
resource "aws_security_group" "alb" {
  name        = "${var.project}-alb-sg"
  description = "Allow HTTP/HTTPS from the internet to the load balancer"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-alb-sg" }
}

# 2) App (EC2): only accepts the app port (8000) from the ALB.
resource "aws_security_group" "app" {
  name        = "${var.project}-app-sg"
  description = "Allow app traffic only from the ALB"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "App port from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-app-sg" }
}

# 3) Database (RDS): only accepts Postgres (5432) from the app tier.
resource "aws_security_group" "db" {
  name        = "${var.project}-db-sg"
  description = "Allow PostgreSQL only from the app"
  vpc_id      = aws_vpc.this.id

  ingress {
    description     = "Postgres from app"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-db-sg" }
}
