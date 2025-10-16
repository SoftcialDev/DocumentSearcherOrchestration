variable "name_prefix" {
  description = "Key Vault name (3-24 chars; letters/numbers/hyphen; globally unique)"
  type        = string
}

variable "location" {
  description = "Azure region, e.g. eastus"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "tenant_id" {
  description = "AAD tenant GUID"
  type        = string
}

variable "sku_name" {
  description = "Key Vault SKU"
  type        = string
  default     = "standard" # or "premium" for HSM-backed keys
}

variable "purge_protection_enabled" {
  description = "Enable purge protection (recommended true for prod)"
  type        = bool
  default     = true
}

variable "soft_delete_retention_days" {
  description = "Soft-delete retention (7-90)"
  type        = number
  default     = 90
}

variable "public_network_access_enabled" {
  description = "Allow public network access"
  type        = bool
  default     = true
}

variable "rbac_enabled" {
  description = "Use RBAC (recommended). If false, uses access policies"
  type        = bool
  default     = true
}

variable "role_assignments" {
  description = <<EOT
RBAC role assignments at the vault scope (used when rbac_enabled=true).
role_definition_name examples:
 - "Key Vault Administrator"
 - "Key Vault Secrets Officer"
 - "Key Vault Secrets User"
 - "Key Vault Reader"
EOT
  type = list(object({
    principal_id         = string
    role_definition_name = string
    principal_type       = optional(string) # "User","ServicePrincipal","Group","ForeignGroup","Device"
  }))
  default = []
}

variable "access_policies" {
  description = "Legacy access policies (used only when rbac_enabled=false)"
  type = list(object({
    object_id              = string
    key_permissions        = optional(list(string), [])
    secret_permissions     = optional(list(string), [])
    certificate_permissions= optional(list(string), [])
    storage_permissions    = optional(list(string), [])
  }))
  default = []
}

variable "secrets" {
  description = "Optional initial secrets to create in the vault"
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
