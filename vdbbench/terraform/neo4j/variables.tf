# https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-variables

variable "project" { }

variable "credentials_file" { }

variable "region" {
  default = "us-central1"
}

variable "zone" {
  default = "us-central1-c"
}
