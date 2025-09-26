terraform {
  required_providers {
    azuread = {
      source  = "hashicorp/azuread"
      version = ">= 2.48.0"
    }
  }
}

data "azuread_client_config" "current" {}

# App registration
resource "azuread_application" "this" {
  display_name = var.display_name

  # SPA platform (for React/MSAL)
  single_page_application {
    redirect_uris = var.redirect_uris
  }

  # Optional: also configure Web platform if you plan to do auth code flow from a backend
  dynamic "web" {
    for_each = var.logout_url != null ? [1] : []
    content {
      redirect_uris = []            # none by default
      logout_url    = var.logout_url
      implicit_grant {
        access_token_issuance_enabled = false
        id_token_issuance_enabled     = true
      }
    }
  }
}