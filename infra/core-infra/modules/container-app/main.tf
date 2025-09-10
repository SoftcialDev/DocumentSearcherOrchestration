resource "azurerm_container_app_environment" "this" {
  name                = "${var.name_prefix}-cae"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_container_app" "this" {
  name                         = "${var.name_prefix}-app"
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"

  ingress {
    external_enabled = true      # must be true for a public URL
    target_port      = var.target_port
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    container {
      name   = "app"
      image  = "docsearchacr.azurecr.io/documentsearcher:latest"
      cpu    = var.cpu
      memory = var.memory

      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
}
