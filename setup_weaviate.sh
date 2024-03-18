#!/bin/bash

echo "setup_weaviate.sh is being executed."
# Kubernetes CLI Installation
echo "Installing kubectl..."
curl -LO "https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl

# Helm Installation
echo "Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

echo "setup_weaviate.sh has been successfully executed."