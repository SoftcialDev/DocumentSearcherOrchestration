variable "name" {
  description = "ACR name (globally unique, 5-50 alphanumeric; lower-case recommended)."
  type        = string
}

variable "resource_group" {
  description = "Resource group name."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "sku" {
  description = "ACR SKU."
  type        = string
  default     = "Standard"
}

variable "admin_enabled" {
  description = "Enable admin user for ACR."
  type        = bool
  default     = true
}
