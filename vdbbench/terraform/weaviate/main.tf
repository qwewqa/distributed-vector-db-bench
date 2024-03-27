terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.20.0"
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
  name = "weaviate-network"
}

resource "google_compute_firewall" "ssh" {
  name    = "weaviate-firewall-ssh"
  network = google_compute_network.default.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "weaviate_api" {
  name    = "weaviate-firewall-api"
  network = google_compute_network.default.name

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"]
}


resource "google_compute_firewall" "internal" {
  name    = "weaviate-firewall-internal"
  network = google_compute_network.default.name

  allow {
    protocol = "all"
  }

  source_tags = ["weaviate"]
}

resource "google_compute_instance" "db_instances" {
  for_each     = toset([for i in range(var.node_count) : tostring(i)])
  name         = "weaviate-${each.key}"
  machine_type = var.machine_type
  tags         = ["weaviate"]
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      type = "pd-ssd"
      size = 128
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
        # Update and install necessary packages
        sudo apt-get update
        sudo apt-get install -y docker.io
        sudo systemctl start docker
        sudo systemctl enable docker

        # Pull and run Weaviate docker image
        sudo docker pull semitechnologies/weaviate:latest
        sudo docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:latest

        # Add any additional setup or configuration below
        ${var.before_start}
        EOF
}

resource "google_compute_instance" "runner_instance" {
  name         = "weaviate-runner"
  machine_type = var.machine_type
  tags         = ["weaviate"]
  allow_stopping_for_update = true

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
}
