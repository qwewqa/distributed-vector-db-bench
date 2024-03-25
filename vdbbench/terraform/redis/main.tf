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
  name = "redis-network"
}

resource "google_compute_firewall" "ssh" {
  name    = "redis-firewall-ssh"
  network = google_compute_network.default.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "internal" {
  name    = "redis-firewall-internal"
  network = google_compute_network.default.name

  allow {
    protocol = "all"
  }

  source_tags = ["redis"]
}

resource "google_compute_instance" "db_instances" {
  for_each     = toset([for i in range(var.node_count) : tostring(i)])
  name         = "redis-${each.key}"
  machine_type = var.machine_type
  tags         = ["redis"]
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
        curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

        echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

        sudo apt-get update
        sudo apt-get install -y redis

        sudo mkdir /redis
        sudo chmod 777 /redis
        cd /redis
        cat <<EOT > /redis/redis1.conf
        port 7000
        cluster-enabled yes
        cluster-config-file /redis/nodes1.conf
        cluster-node-timeout 5000
        protected-mode no
        EOT
        cat <<EOT > /redis/redis2.conf
        port 7001
        cluster-enabled yes
        cluster-config-file /redis/nodes2.conf
        cluster-node-timeout 5000
        protected-mode no
        EOT

        redis-server /redis/redis1.conf --daemonize yes
        redis-server /redis/redis2.conf --daemonize yes

        redis-cli --cluster create \
          ${join(" ", [for i in range(var.node_count) : "redis-${i}:7000"])} \
          ${join(" ", [for i in range(var.node_count) : "redis-${i}:7001"])} \
          --cluster-replicas 1 --cluster-yes
        EOF
}

resource "google_compute_instance" "runner_instance" {
  name         = "redis-runner"
  machine_type = var.machine_type
  tags         = ["redis"]
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
