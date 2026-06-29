# Look up the latest Amazon Linux 2023 AMI ID from the public SSM parameter
# AWS maintains. This way we always get the newest patched image.
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "this" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = var.instance_profile_name

  # The boot script that installs Docker and runs our container.
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    region                = var.region
    image_uri             = var.image_uri
    ssm_database_url_path = var.ssm_database_url_path
  })

  # Replace the instance if the boot script changes.
  user_data_replace_on_change = true

  tags = { Name = "${var.project}-backend" }
}
