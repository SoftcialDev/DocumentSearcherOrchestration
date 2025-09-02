########################################
# Global Configuration (shared across modules)
########################################
variable "name_prefix" {
  description = "Prefix used for naming all provisioned resources. Must comply with Azure naming rules."
  type        = string
  default     = "document-search"
}

variable "region" {
  description = "Azure region where all resources will be deployed, for example 'eastus'."
  type        = string
  default     = "eastus"
}

variable "database_url" {
  description = "Database connection URL"
  type        = string
}

variable "tags" {
  description = "Map of tags to apply to all Azure resources."
  type        = map(string)
  default     = {}
}

########################################
# Networking Module (May not be needed?)
########################################
variable "vnet_ip" {
  description = "Base IP address range of the Virtual Network, for example '10.26.0.0'."
  type        = string
  default     = "10.26.0.0"
}

variable "vnet_mask" {
  description = "CIDR mask for the Virtual Network, for example '/16'."
  type        = string
  default     = "/16"
}

variable "subnet_mask" {
  description = "CIDR mask for subnets within the VNet, for example '/20'."
  type        = string
  default     = "/20"
}


########################################
# Azure Active Directory (AAD) Module
########################################
variable "aad_app_name" {
  description = "Name of the Azure AD application."
  type        = string
}

variable "aad_redirect_uris" {
  description = "List of redirect URIs allowed for the Azure AD application."
  type        = list(string)
}

variable "aad_desktop_redirect_uris" {
  description = "List of redirect URIs for the SPA (e.g., http://localhost:5173, https://prod-domain/.../auth)"
  type        = list(string)
}

variable "aad_logout_uris" {
  description = "List of post-logout redirect URIs for the Azure AD application."
  type        = list(string)
}

variable "aad_admins_group_members" {
  description = "List of user principal names (UPNs) to add to the Admins group."
  type        = list(string)
}


variable "aad_enable_directory_role_assignment" {
  description = "Whether to assign directory roles (e.g., 'User Administrator') to the Admins group."
  type        = bool
  default     = false
}


########################################
# PostgreSQL Module
########################################
variable "postgres_admin_username" {
  description = "Administrator username for PostgreSQL Flexible Server."
  type        = string
}

variable "postgres_admin_password" {
  description = "Administrator password for PostgreSQL Flexible Server."
  type        = string
  sensitive   = true
}

variable "postgres_version" {
  description = "PostgreSQL major version, for example '13' or '14'."
  type        = string
  default     = "13"
}

variable "postgres_sku_name" {
  description = "SKU name for PostgreSQL Flexible Server, for example 'Standard_D2s_v3'."
  type        = string
  default     = "Standard_D2s_v3"
}

variable "postgres_storage_mb" {
  description = "Storage size in MB for PostgreSQL Flexible Server."
  type        = number
  default     = 32768
}

variable "postgres_vnet_subnet_id" {
  description = "Resource ID of a subnet delegated for private PostgreSQL access. Leave empty for public access."
  type        = string
  default     = ""
}

variable "postgres_public_network_access" {
  description = "Whether to allow public network access: 'Enabled' or 'Disabled'."
  type        = string
  default     = "Enabled"
}

variable "postgres_allowed_ips" {
  description = "List of client IP addresses or CIDRs to allow when public access is enabled, e.g. ['203.0.113.5/32']. Empty list means no public IP allowed."
  type        = list(string)
  default     = []
}

########################################
# Azure Container Registry (ACR)
########################################
variable "acr_sku" {
  description = "ACR SKU: Basic, Standard, Premium."
  type        = string
  default     = "Basic"
}

variable "acr_admin_enabled" {
  description = "Enable ACR admin account (dev convenience; disable for prod with Managed Identity)."
  type        = bool
  default     = true
}


########################################
# Function App Module
########################################
variable "function_plan_sku_tier" {
  description = "App Service Plan SKU tier for Function App: 'Dynamic' for Consumption or 'ElasticPremium' for Premium."
  type        = string
  default     = "Dynamic"
}

variable "function_plan_sku_size" {
  description = "App Service Plan SKU size for Function App: 'Y1' for Consumption or 'EP1' for Premium."
  type        = string
  default     = "Y1"
}

variable "function_vnet_subnet_id" {
  description = "Resource ID of the subnet for Function App VNet Integration, if needed for private resource access."
  type        = string
  default     = ""
}