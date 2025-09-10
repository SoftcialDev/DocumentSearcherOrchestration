resource "random_string" "acr_suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_container_registry" "container_registry" {
  name                = "${var.name}${random_string.acr_suffix.result}"
  resource_group_name = var.resource_group
  location            = var.location
  sku                 = var.sku
  admin_enabled       = var.admin_enabled
}
