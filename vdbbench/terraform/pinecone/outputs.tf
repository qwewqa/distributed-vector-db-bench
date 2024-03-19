output "pinecone_instance_public_ips" {
  value = google_compute_instance.pinecone_instance[*].network_interface[*].access_config.0.nat_ip
}
