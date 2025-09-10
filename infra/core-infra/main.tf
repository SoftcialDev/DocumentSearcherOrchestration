resource "azurerm_resource_group" "main-rg" {
  # Use a consistent prefix for naming, supplied by var.name_prefix
  name     = var.name_prefix
  # Deploy the resource group in the region provided by var.region
  location = var.region
}

# Retrieve details about the current Azure AD tenant and client,
# so we can reference the tenant ID and object ID in later modules.
data "azuread_client_config" "current" {}

module "network" {
  source      = "./modules/network"
  # Prefix used by the network module for naming VNet, subnets, etc.
  name_prefix = var.name_prefix
  # Region to deploy the VNet and subnets
  region      = var.region
  # Associate this network with the resource group we just created
  resource_group  = azurerm_resource_group.main-rg.name
}

#module "container_registry" {
#  source              = "./modules/acr"
#  name                = var.name_prefix
#  resource_group      = azurerm_resource_group.main-rg.name
#  location            = "eastus2"
#  sku                 = var.acr_sku
#}

module "container_app" {
  source              = "./modules/container-app"
  name_prefix         = var.name_prefix
  location            = var.region
  resource_group_name = azurerm_resource_group.main-rg.name

  # Pull from ACR created by your ACR module
  registry_server   = module.container_registry.login_server
  registry_username = module.container_registry.admin_username
  registry_password = module.container_registry.admin_password

  # Use your existing all-in-one image + serving port
  image       = "${module.container_registry.login_server}/documentsearcher:latest"
  target_port = 3000  # <-- change if your container listens on another port

  # Optional: runtime sizing
  cpu    = 2.0
  memory = "4Gi"

  # Optional: env vars (example with Postgres)
  env = {
    PGHOST    = module.postgres.postgres_fqdn
    PGDATABASE= module.postgres.database_name
    PGUSER    = var.postgres_admin_username
    PGPASSWORD= var.postgres_admin_password
    PGSSLMODE = "require"
  }
}

module "postgres" {
  source = "./modules/database"
  # Naming prefix and resource group for the database
  name_prefix         = var.name_prefix
  resource_group_name = azurerm_resource_group.main-rg.name
  # Deploy the DB in westus3 for isolation or latency reasons
  location            = "westus3"
  # Admin credentials and version for PostgreSQL
  admin_username      = var.postgres_admin_username
  admin_password      = var.postgres_admin_password
  postgres_version    = var.postgres_version
  sku_name            = var.postgres_sku_name
  storage_mb          = var.postgres_storage_mb
  # Optional VNet integration for private DB access
  # vnet_subnet_id      = var.postgres_vnet_subnet_id
  public_network_access = var.postgres_public_network_access
  # Restrict public access to specific IP ranges
  allowed_ips         = var.postgres_allowed_ips
}