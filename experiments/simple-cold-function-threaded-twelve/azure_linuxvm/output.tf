# output ip address
output "ip_address" {
  value = azurerm_linux_virtual_machine.simple-cold-function-threaded-twelve-worker.public_ip_address
}
