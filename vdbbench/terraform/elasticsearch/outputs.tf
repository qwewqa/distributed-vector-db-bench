output "network_name" {
  value       = google_compute_network.default.name
  description = "The name of the network created for Elasticsearch."
}

output "firewall_ssh_name" {
  value       = google_compute_firewall.ssh.name
  description = "The name of the SSH firewall rule."
}

output "firewall_internal_name" {
  value       = google_compute_firewall.internal.name
  description = "The name of the internal firewall rule."
}

output "elasticsearch_instance_names" {
  value = [for instance in google_compute_instance.db_instances : instance.name]
  description = "The names of the Elasticsearch instances."
}

output "elasticsearch_instance_ips" {
  value = [for instance in google_compute_instance.db_instances : instance.network_interface[0].access_config[0].nat_ip]
  description = "The external IP addresses of the Elasticsearch instances."
}

output "runner_instance_name" {
  value       = google_compute_instance.runner_instance.name
  description = "The name of the runner instance."
}

output "runner_instance_ip" {
  value       = google_compute_instance.runner_instance.network_interface[0].access_config[0].nat_ip
  description = "The external IP address of the runner instance."
}
