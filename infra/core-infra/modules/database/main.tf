locals {
  # Normalize IP/CIDR entries like "203.0.113.5/32" -> "203.0.113.5"
  allowed_ip_addrs = [for ip in var.allowed_ips : split("/", ip)[0]]
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "postgres_server" {
  name                = "${var.name_prefix}-postgres-server-flexible"
  location            = var.location
  resource_group_name = var.resource_group_name
  version             = var.postgres_version

  administrator_login    = var.admin_username
  administrator_password = var.admin_password

  sku_name   = var.sku_name # e.g. B_Standard_B1ms / GP_Standard_D2s_v3
  storage_mb = var.storage_mb

  public_network_access_enabled = var.public_network_access == "Enabled"
  backup_retention_days         = 7

  lifecycle {
    ignore_changes = [
      zone,
      high_availability[0].standby_availability_zone,
    ]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-postgres"
  })
}

# Allow Azure services (special 0.0.0.0 rule) only when public access is Enabled
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  count            = var.public_network_access == "Enabled" ? 1 : 0
  name             = "${var.name_prefix}-fw-azure-services"
  server_id        = azurerm_postgresql_flexible_server.postgres_server.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Client IP firewall rules when public access is Enabled
resource "azurerm_postgresql_flexible_server_firewall_rule" "postgres_firewall" {
  for_each         = var.public_network_access == "Enabled" ? toset(local.allowed_ip_addrs) : []
  name             = "${var.name_prefix}-fw-${replace(each.value, ".", "-")}"
  server_id        = azurerm_postgresql_flexible_server.postgres_server.id
  start_ip_address = each.value
  end_ip_address   = each.value
}

# Create a database on the server (correct resource type)
resource "azurerm_postgresql_flexible_server_database" "postgres_database" {
  name      = var.db_name
  server_id = azurerm_postgresql_flexible_server.postgres_server.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}
