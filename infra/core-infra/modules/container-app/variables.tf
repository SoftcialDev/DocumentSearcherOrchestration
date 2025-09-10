variable "name_prefix"         { type = string }
variable "resource_group_name" { type = string }
variable "location"            { type = string }

# Image & runtime
variable "image"{ 
  type = string 
  default = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}
variable "target_port" { type = number }                   # e.g. 3000 or 8000

variable "cpu"{ 
  type = number
  default = 2.0 
}

variable "memory"{ 
  type = string
  default = "4Gi"
}

variable "min_replicas"{ 
  type = number
  default = 0 
}

variable "max_replicas"{
 type = number  
 default = 3 
}

variable "env"{ 
  type = map(string)
  default = {} 
}

# ACR creds (quickest path)
variable "registry_server"   { type = string }             # e.g. "myacr.azurecr.io"
variable "registry_username" { type = string }
variable "registry_password" { type = string }
