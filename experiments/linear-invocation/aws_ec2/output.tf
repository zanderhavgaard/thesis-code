output "ip_address" {
  value = aws_eip.linear-invocation1-worker-eip.public_ip
}
