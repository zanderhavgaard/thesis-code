# output ip address
output "ip_address" {
  value = azurerm_linux_virtual_machine.weakest-link-openfaas-worker.public_ip_address
}
