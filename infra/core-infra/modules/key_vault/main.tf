resource "azurerm_key_vault" "this" {
  name                       = "${var.name_prefix}-kv"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = var.sku_name
  purge_protection_enabled   = var.purge_protection_enabled
  soft_delete_retention_days = var.soft_delete_retention_days
  public_network_access_enabled = var.public_network_access_enabled

  # RBAC vs Access Policies
  enable_rbac_authorization = var.rbac_enabled

  dynamic "access_policy" {
    for_each = var.rbac_enabled ? [] : var.access_policies
    content {
      tenant_id               = var.tenant_id
      object_id               = access_policy.value.object_id
      key_permissions         = try(access_policy.value.key_permissions, [])
      secret_permissions      = try(access_policy.value.secret_permissions, [])
      certificate_permissions = try(access_policy.value.certificate_permissions, [])
      storage_permissions     = try(access_policy.value.storage_permissions, [])
    }
  }

  tags = var.tags
}

resource "azurerm_role_assignment" "this" {
  for_each = var.rbac_enabled ? {
    # use a stable, known-at-plan key (the index as a string)
    for idx, ra in var.role_assignments : tostring(idx) => ra
  } : {}

  scope               = azurerm_key_vault.this.id
  role_definition_name = each.value.role_definition_name
  principal_id        = each.value.principal_id
  principal_type      = try(each.value.principal_type, null)

  # Uncomment if you hit propagation/race issues with fresh identities:
  # skip_service_principal_aad_check = true
}

# Optional initial secrets
resource "azurerm_key_vault_secret" "this" {
  for_each     = var.secrets
  name         = each.key
  value        = each.value
  key_vault_id = azurerm_key_vault.this.id

  depends_on = [
    azurerm_role_assignment.this
  ]
}
