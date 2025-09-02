variable "name_prefix" {
  description = "Prefix for naming."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "resource_group_name" {
  description = "Target resource group."
  type        = string
}

variable "postgres_version" {
  description = "PostgreSQL major version (e.g., 16)."
  type        = string
  default     = "16"
}

variable "admin_username" {
  description = "Admin username."
  type        = string
}

variable "admin_password" {
  description = "Admin password."
  type        = string
  sensitive   = true
}

variable "sku_name" {
  description = "Flexible Server SKU (e.g., B_Standard_B1ms, GP_Standard_D2s_v3)."
  type        = string
}

variable "storage_mb" {
  description = "Storage in MB."
  type        = number
  default     = 32768
}

variable "public_network_access" {
  description = "Enabled or Disabled."
  type        = string
  default     = "Enabled"
}

variable "allowed_ips" {
  description = "List of client IPs or CIDRs to allow when public access is Enabled."
  type        = list(string)
  default     = []
}

variable "db_name" {
  description = "Database name to create."
  type        = string
  default     = "docsearch"
}

variable "tags" {
  description = "Tags to apply."
  type        = map(string)
  default     = {}
}
