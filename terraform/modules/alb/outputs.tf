output "alb_dns_name" {
  description = "Public DNS name of the load balancer"
  value       = aws_lb.this.dns_name
}

output "target_group_arn" {
  value = aws_lb_target_group.this.arn
}
