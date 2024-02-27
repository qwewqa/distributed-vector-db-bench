variable "pinecone_api_key" {
  type        = string
  description = "The pinecone API key used for this instance"
  sensitive = true
}

variable "pinecone_environment" {
  type = string
}
