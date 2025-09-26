output "object_id" {
  description = "Application object ID"
  value       = azuread_application.this.id
}

# MSAL authority you’ll use in React: https://login.microsoftonline.com/<tenant-id>
output "authority" {
  description = "MSAL authority URL"
  value       = "https://login.microsoftonline.com/${data.azuread_client_config.current.tenant_id}"
}
