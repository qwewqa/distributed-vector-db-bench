terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 3.5"
    }
  }

  required_version = ">= 0.12"
}

provider "google" {
  credentials = file("<PATH-TO-YOUR-CREDENTIALS-FILE>")
  project     = "<YOUR-GCP-PROJECT-ID>"
  region      = "us-central1"
}

resource "google_compute_instance" "weaviate_instance" {
  name         = "weaviate-instance"
  machine_type = "e2-medium"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral IP
    }
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    sudo apt-get update
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.13.2
    EOF
}

output "instance_ip" {
  value = google_compute_instance.weaviate_instance.network_interface[0].access_config[0].nat_ip
}
