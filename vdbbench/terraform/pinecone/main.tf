terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.51.0"
    }
    pinecone = {
      source = "thekevinwang.com/terraform-providers/pinecone"
    }
  }
}

// pinecone_api_key = "fixme"
// pinecone_environment = "us-west4-gcp-free"
provider "pinecone" {
  apikey      = var.pinecone_api_key
  environment = var.pinecone_environment
}

resource "pinecone_index" "my-first-index" {
  name      = "testidx"
  dimension = 1536
  metric    = "cosine"
  pods      = 1
}