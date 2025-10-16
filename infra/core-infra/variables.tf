variable "name_prefix" {
  description = "Short project prefix for resource names (alphanumeric, 3-12 chars)."
  type        = string
}

variable "region" {
  description = "Azure region for resources."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group to create."
  type        = string
  default     = null
}

variable "tags" {
  description = "Map of tags to apply to all Azure resources."
  type        = map(string)
  default     = {}
}

#
# Entra ID App
#
variable "app_display_name" {
  type        = string
  description = "Display name for the Entra ID application"
}

variable "redirect_uris" {
  type        = list(string)
  description = "SPA redirect URIs"
  default     = [
    "http://localhost:3000/"
  ]
}

variable "logout_url" {
  type        = string
  description = "Optional front-channel logout URL"
  default     = null
}

#######################
# Azure Container App #
#######################
variable "acr_login_server" {
  description = "value"
  type = string
}

variable "acr_admin_username" {
  description = "value"
  type = string
}

variable "acr_admin_password" {
  description = "value"
  type = string
}

variable "acr_image"{
  description = "value"
  type = string
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

####################
# Azure connection #
####################
variable "subscription_id" { 
  type = string 
}
variable "tenant_id" { 
  type = string 
}

##############
# User Input #
##############
