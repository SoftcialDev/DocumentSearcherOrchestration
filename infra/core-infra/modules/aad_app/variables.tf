variable "display_name" {
  description = "Display name of the Entra ID application"
  type        = string
}

variable "redirect_uris" {
  description = "Redirect URIs for the SPA (e.g., https://your.domain/, http://localhost:3000)"
  type        = list(string)
  default     = ["https://documentsearcher.softcial.com/"]
}

variable "logout_url" {
  description = "Front-channel logout URL (optional)"
  type        = string
  default     = null
}
