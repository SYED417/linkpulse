# The Application Load Balancer itself: internet-facing, spread across both
# public subnets, protected by the ALB security group (open on 80/443).
resource "aws_lb" "this" {
  name               = "${var.project}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.security_group_id]
  subnets            = var.subnet_ids
  tags               = { Name = "${var.project}-alb" }
}

# A target group is the pool of backends the ALB forwards traffic to.
# It health-checks each target by calling GET /health and expecting HTTP 200.
resource "aws_lb_target_group" "this" {
  name        = "${var.project}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = { Name = "${var.project}-tg" }
}

# The listener watches port 80 and forwards all requests to the target group.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# Register our EC2 instance into the target group on port 8000.
resource "aws_lb_target_group_attachment" "this" {
  target_group_arn = aws_lb_target_group.this.arn
  target_id        = var.instance_id
  port             = 8000
}
