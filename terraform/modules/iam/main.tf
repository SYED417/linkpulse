# Trust policy: allow EC2 instances to assume this role.
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = "${var.project}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = { Name = "${var.project}-ec2-role" }
}

# AWS-managed policy enabling Systems Manager Session Manager: lets you open
# a shell on the instance from the console/CLI WITHOUT opening SSH (port 22).
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Allows the instance to pull images from Amazon ECR (read-only).
resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# Custom policy: read this project's secrets from SSM Parameter Store
# (we'll store DATABASE_URL there in a later step).
data "aws_iam_policy_document" "ssm_params" {
  statement {
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]
    resources = ["arn:aws:ssm:*:*:parameter/${var.project}/*"]
  }
}

resource "aws_iam_role_policy" "ssm_params" {
  name   = "${var.project}-ssm-read"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ssm_params.json
}

# An instance profile is the wrapper that lets an EC2 instance use the role.
resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project}-ec2-profile"
  role = aws_iam_role.ec2.name
}
