output "name" {
  value = azurerm_container_app.this.name
}

output "fqdn" {
  value = azurerm_container_app.this.ingress[0].fqdn
}

output "url" {
  value = "https://${azurerm_container_app.this.ingress[0].fqdn}/"
}

output "identity_principal_id" {
  description = "System-assigned managed identity principal ID for the Container App"
  value       = azurerm_container_app.this.identity[0].principal_id
}