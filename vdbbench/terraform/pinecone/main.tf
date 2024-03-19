# terraform {
#   required_providers {
#     google = {
#       source  = "hashicorp/google"
#       version = "4.51.0"
#     }
#     pinecone = {
#       source = "thekevinwang.com/terraform-providers/pinecone"
#     }
#   }
# }

# // pinecone_api_key = "fixme"
# // pinecone_environment = "us-west4-gcp-free"
# provider "pinecone" {
#   apikey      = var.pinecone_api_key
#   environment = var.pinecone_environment
# }

# resource "pinecone_index" "my-first-index" {
#   name      = "testidx"
#   dimension = 1536
#   metric    = "cosine"
#   pods      = 1
# }

# provider "google" {
#   credentials = var.credentials != "" ? file(var.credentials) : null

  # project = var.project
  # region  = var.region
  # zone    = var.zone
# }

# resource "google_compute_network" "default" {
#   name = "pinecone-network"
# }

# resource "google_compute_firewall" "ssh" {
#   name    = "pinecone-firewall-ssh"
#   network = google_compute_network.default.name

#   allow {
#     protocol = "tcp"
#     ports    = ["22"]
#   }

#   source_ranges = ["0.0.0.0/0"]
# }

# resource "google_compute_firewall" "internal" {
#   name    = "pinecone-firewall-internal"
#   network = google_compute_network.default.name

#   allow {
#     protocol = "all"
#   }

#   source_tags = ["pinecone"]
# }

# resource "google_compute_instance" "db_instances" {
#   for_each     = toset([for i in range(var.node_count) : tostring(i)])
#   name         = "pinecone-${each.key}"
#   machine_type = var.machine_type
#   tags         = ["pinecone"]

#   boot_disk {
#     initialize_params {
#       image = "ubuntu-os-cloud/ubuntu-2204-lts"
#     }
#   }

#   network_interface {
#     network = google_compute_network.default.name
#     access_config {
#       // Ephemeral IP
#     }
#   }

#   metadata = {
#     ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
#   }

#   # metadata_startup_script = <<-EOF
#   #       #!/bin/bash
#   #       wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
#   #       echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
#   #       sudo apt-get update
#   #       sudo apt-get install elasticsearch -y

#   #       sudo cat <<EOT > /etc/elasticsearch/elasticsearch.yml
#   #       path.data: "/var/lib/elasticsearch"
#   #       path.logs: "/var/log/elasticsearch"
#   #       xpack.security.enabled: false
#   #       xpack.security.autoconfiguration.enabled: false
#   #       http.host: 0.0.0.0
#   #       cluster.name: "elasticsearch"
#   #       node.name: "elasticsearch-${each.key}"
#   #       network.host: 0.0.0.0
#   #       discovery.seed_hosts: ["${join("\", \"", [for i in range(var.node_count) : "elasticsearch-${i}"])}"]
#   #       cluster.initial_master_nodes: ["${join("\", \"", [for i in range(var.node_count) : "elasticsearch-${i}"])}"]
#   #       EOT

#   #       # Remove the default keystore since we're disabling security
#   #       sudo rm /etc/elasticsearch/elasticsearch.keystore
#   #       sudo /usr/share/elasticsearch/bin/elasticsearch-keystore create
        
#   #       ${var.before_start}

#   #       sudo systemctl start elasticsearch
#   #       sudo systemctl enable elasticsearch
#   #       EOF

#   metadata_startup_script = <<-SCRIPT
#     #!/bin/bash
#     # Install Pinecone Vector Database
#     wget https://dl.pinecone.io/cli/install.sh
#     chmod +x install.sh
#     ./install.sh
#     systemctl start pinecone
#     systemctl enable pinecone
#   SCRIPT
# }

# resource "google_compute_instance" "runner_instance" {
#   name         = "pinecone-runner"
#   machine_type = var.machine_type
#   tags         = ["pinecone"]

#   boot_disk {
#     initialize_params {
#       image = "ubuntu-os-cloud/ubuntu-2204-lts"
#     }
#   }

#   network_interface {
#     network = google_compute_network.default.name
#     access_config {
#       // Ephemeral IP
#     }
#   }

#   metadata = {
#     ssh-keys = "${var.ssh_user}:${var.ssh_public_key}"
#   }

#   metadata_startup_script = <<-EOF
#         #!/bin/bash
#         mkdir -p /vdbbench
#         echo "test" > /vdbbench/test.txt
#         EOF
# }

# using ChatGPT generated code

provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}



resource "google_compute_instance" "pinecone_instance" {
  count        = var.node_count
  name         = "pinecone-instance-${count.index + 1}"
  machine_type = var.machine_type
  zone         = var.zone
  
  tags = ["pinecone"]

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

  metadata_startup_script = <<-SCRIPT
    #!/bin/bash
    # Install Pinecone Vector Database
    wget https://dl.pinecone.io/cli/install.sh
    chmod +x install.sh
    ./install.sh
    # Configure Pinecone (replace with actual configuration)
    pinecone setup --api-key=<YOUR_API_KEY> --api-secret=<YOUR_API_SECRET> --project-id=<YOUR_PROJECT_ID>
    systemctl start pinecone
    systemctl enable pinecone
  SCRIPT
}

resource "google_compute_firewall" "pinecone_firewall" {
  name    = "pinecone-firewall"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["3001", "4000"]
  }

  source_tags = ["pinecone"]
}

output "pinecone_instance_public_ips" {
  value = google_compute_instance.pinecone_instance[*].network_interface[*].access_config.0.nat_ip
}
