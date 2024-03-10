# https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-build
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
  }
}

provider "google" {
  credentials = var.credentials != "" ? file(var.credentials) : null

  project = var.project
  region  = var.region
  zone    = var.zone
}

resource "google_compute_network" "default" {
  name = "tigergraph-network"
}

resource "google_compute_firewall" "ssh" {
  name    = "tigergraph-firewall-ssh"
  network = google_compute_network.default.name

  allow {
    protocol = "tcp"
    ports    = ["22", "14240"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "tigergraph_internal" {
  name    = "tigergraph-firewall-internal"
  network = google_compute_network.default.name

  allow {
    protocol = "all"
  }

  source_tags = ["tigergraph"]
}

resource "google_compute_instance" "tigergraph_instance" {
  name         = "tigergraph-server"
  machine_type = var.machine_type
  tags         = ["tigergraph"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network = google_compute_network.default.name
    access_config {
      // Ephemeral IP
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }

  metadata_startup_script = <<-EOF
        #!/bin/bash
        # Install Docker (TigerGraph runs in a Docker container)
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        sudo apt-get update
        sudo apt-get install -y docker-ce

        # Download and run the TigerGraph Docker container
        sudo docker run -d --name tigergraph -p 9000:9000 -p 14240:14240 tigergraph/tigergraph:latest

        # Additional configuration steps can be added here
        EOF
}

variable "credentials" {
  description = "Path to the Google Cloud credentials JSON file."
}

variable "project" {
  description = "The Google Cloud project ID."
}

variable "region" {
  description = "The Google Cloud region for resources."
}

variable "zone" {
  description = "The Google Cloud zone for the resources."
}

variable "machine_type" {
  description = "The machine type to use for the TigerGraph server."
  default     = "e2-medium"
}

variable "ssh_user" {
  description = "SSH username for accessing the instances."
}

variable "ssh_public_key" {
  description = "SSH public key for the SSH user."
}
