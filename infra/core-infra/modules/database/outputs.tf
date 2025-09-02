output "fqdn" {
  value = azurerm_postgresql_flexible_server.postgres_server.fqdn
}

output "server_name" {
  value = azurerm_postgresql_flexible_server.postgres_server.name
}

output "admin_username" {
  value = var.admin_username
}

# Avoid echoing passwords unless you truly need it.
# output "admin_password" {
#   value     = var.admin_password
#   sensitive = true
# }

output "database_name" {
  value = azurerm_postgresql_flexible_database.postgres_database.name
}

# Ready-to-use connection string (SSL required by Flexible Server)
output "connection_string" {
  value     = "postgresql://${var.admin_username}:${var.admin_password}@${azurerm_postgresql_flexible_server.postgres_server.fqdn}:5432/${azurerm_postgresql_flexible_database.postgres_database.name}?sslmode=require"
  sensitive = true
}
