variable "credentials" {
  type        = string
  description = "The path to the service account key file"
  default = ""
}

variable "project" {
  type        = string
  description = "The project ID to deploy resources into"
}

variable "region" {
  type        = string
  description = "The region to deploy resources into"
  default     = "us-west1"
}

variable "zone" {
  type        = string
  description = "The zone to deploy resources into"
  default     = "us-west1-b"
}

variable "machine_type" {
  type        = string
  description = "The machine type to use for the instance"
  default     = "n2-standard-2"
}

variable "node_count" {
  type        = number
  description = "The number of nodes to deploy"
  default     = 3
}

variable "before_start" {
  type        = string
  description = "Added to the startup script before starting the service"
  default     = ""
}

variable "ssh_user" {
  type        = string
  description = "The SSH user to use for the instances"
  default     = "vdbbench"
}

variable "ssh_public_key" {
  type        = string
  description = "The SSH public key to use for the instances"
  
}
