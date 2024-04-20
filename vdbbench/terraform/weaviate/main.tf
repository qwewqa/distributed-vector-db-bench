terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.20.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
    }
    helm = {
      source  = "hashicorp/helm"
    }
  }
  required_version = ">= 1.0"
}

provider "google" {
  credentials = var.credentials != "" ? file(var.credentials) : null

  project = var.project
  region  = var.region
  zone    = var.zone
}


resource "google_container_cluster" "weaviate_cluster" {
  name     = "weaviate-cluster"
  location = var.region

  # Set this to false to disable deletion protection
  deletion_protection = false

  initial_node_count = 1

  node_config {
    machine_type = var.machine_type
    disk_size_gb = 50
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    tags = ["weaviate"]
  }

}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.weaviate_cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.weaviate_cluster.master_auth.0.cluster_ca_certificate)
}

data "kubernetes_service" "weaviate" {
  metadata {
    name = "weaviate"
  }
}

data "google_client_config" "default" {}

provider "helm" {
  kubernetes {
    host                   = google_container_cluster.weaviate_cluster.endpoint
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(google_container_cluster.weaviate_cluster.master_auth.0.cluster_ca_certificate)
  }
}

resource "helm_release" "weaviate" {
  name       = "weaviate"
  repository = "https://weaviate.github.io/weaviate-helm"
  chart      = "weaviate"
  version    = "16.8.8"

  set {
    name  = "replicaCount"
    value = "1"
  }

  set {
    name  = "service.type"
    value = "LoadBalancer"
  }
}

# add code for runner instance
resource "google_compute_instance" "runner_instance" {
  name         = "weaviate-runner"
  machine_type = var.machine_type  # Using the same machine type as the cluster nodes
  zone         = var.zone
  tags         = ["weaviate"]

  network_interface {
    network = google_compute_network.default.name
    access_config {
      // This block is empty to assign a public IP
    }
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  metadata = {
    ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
  }
}

resource "google_compute_network" "default" {
  name = "weaviate-network"
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "ssh"
  network = google_compute_network.default.name

  allow {
    protocol = "tcp"
    ports    = ["22", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]  # Caution: This allows SSH from any IP. Adjust accordingly based on your security requirements.
  target_tags   = ["weaviate"]
}
