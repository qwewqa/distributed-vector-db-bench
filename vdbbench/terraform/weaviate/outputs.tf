output "cluster_endpoint" {
  value = google_container_cluster.weaviate_cluster.endpoint
  description= "The endpoint of the Kubernetes cluster"
}

output "weaviate_endpoint" {
  value = "http://${google_container_cluster.weaviate_cluster.endpoint}:8080"
  description= "The endpoint of the Weaviate cluster"
}

output "runner_instance_ip" {
  value = google_compute_instance.runner_instance.network_interface.0.access_config.0.nat_ip
  description="The public IP of the runner instance"
}

output "weaviate_external_ip" {
  value = data.kubernetes_service.weaviate.status.0.load_balancer.0.ingress.0.ip
}

