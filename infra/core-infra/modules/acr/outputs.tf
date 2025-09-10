output "id" {
  value = azurerm_container_registry.container_registry.id
}

output "name" {
  value = azurerm_container_registry.container_registry.name
}

output "login_server" {
  value = azurerm_container_registry.container_registry.login_server
}

output "admin_username" {
  value       = azurerm_container_registry.container_registry.admin_username
  description = "ACR admin username (requires admin_enabled = true)"
}

output "admin_password" {
  value       = azurerm_container_registry.container_registry.admin_password
  sensitive   = true
  description = "ACR admin password (requires admin_enabled = true)"
}