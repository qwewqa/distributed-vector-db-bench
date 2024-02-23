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
  name = "elasticsearch-network"
}

resource "google_compute_firewall" "ssh" {
  name    = "elasticsearch-firewall-ssh"
  network = google_compute_network.default.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "internal" {
  name    = "elasticsearch-firewall-internal"
  network = google_compute_network.default.name

  allow {
    protocol = "all"
  }

  source_tags = ["elasticsearch"]
}

resource "google_compute_instance" "db_instances" {
  for_each     = toset([for i in range(var.node_count) : tostring(i)])
  name         = "elasticsearch-${each.key}"
  machine_type = var.machine_type
  tags         = ["elasticsearch"]

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
        wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
        sudo apt update
        sudo apt install elasticsearch -y

        sudo cat <<EOT > /etc/elasticsearch/elasticsearch.yml
        path.data: "/var/lib/elasticsearch"
        path.logs: "/var/log/elasticsearch"
        xpack.security.enabled: false
        xpack.security.autoconfiguration.enabled: false
        http.host: 0.0.0.0
        cluster.name: "elasticsearch"
        node.name: "elasticsearch-${each.key}"
        network.host: 0.0.0.0
        discovery.seed_hosts: ["${join("\", \"", [for i in range(var.node_count) : "elasticsearch-${i}"])}"]
        cluster.initial_master_nodes: ["${join("\", \"", [for i in range(var.node_count) : "elasticsearch-${i}"])}"]
        EOT

        # Remove the default keystore since we're disabling security
        sudo rm /etc/elasticsearch/elasticsearch.keystore
        sudo /usr/share/elasticsearch/bin/elasticsearch-keystore create
        
        ${var.before_start}

        sudo systemctl start elasticsearch
        sudo systemctl enable elasticsearch
        EOF
}

resource "google_compute_instance" "runner_instance" {
  name         = "elasticsearch-runner"
  machine_type = var.machine_type
  tags         = ["elasticsearch"]

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
        mkdir -p /vdbbench
        echo "test" > /vdbbench/test.txt
        EOF
}
