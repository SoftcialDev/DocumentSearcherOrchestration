output "acr_login_server" {
  description = "ACR login server (push/pull endpoint)."
  value       = module.container_registry.login_server
}

output "acr_id" {
  value = module.container_registry.id
}
