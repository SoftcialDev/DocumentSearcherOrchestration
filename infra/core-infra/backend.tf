terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg-document-searcher"
    storage_account_name = "tfstateaccdsz41ipc"
    container_name       = "tfstate-document-search"
    key                  = "core-infra-prod.tfstate"
  }
}