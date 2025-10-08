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

  secret {
    name  = "acr-pwd"
    value = var.registry_password
  }
  registry {
    server               = var.registry_server
    username             = var.registry_username
    password_secret_name = "acr-pwd"
  }

  ingress {
    external_enabled = true
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
      image  = var.image
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
