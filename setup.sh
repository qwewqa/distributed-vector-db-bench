#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script is being executed directly. Please source this file instead."
    exit 1
fi

PROJECT=$1

if [ -z "$PROJECT" ]; then
    echo "Please provide a project ID as an argument."
    return 1
fi

if [ ! -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    echo "Please login to gcloud."
    gcloud auth application-default login
else
    echo "Already logged in"
fi

echo "Project: ${PROJECT}"
gcloud config set project ${PROJECT}

private_key_path="$(pwd)/id_rsa"
public_key_path="$(pwd)/id_rsa.pub"

if [[ -f "$private_key_path" && -f "$public_key_path" ]]; then
    echo "SSH key pair already exists in the current directory, skipping creation."
else
    # Generate a new SSH key pair
    echo "Creating a new SSH key pair..."
    ssh-keygen -t rsa -b 4096 -f "$private_key_path" -N ""
    echo "SSH key pair created successfully."
fi
chmod 600 ${private_key_path}

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    . venv/bin/activate
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    pip install ruff
elif [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating existing virtual environment..."
    . venv/bin/activate
fi

export TF_VAR_project=${PROJECT}
export TF_VAR_ssh_public_key=$(cat $public_key_path)
export TF_VAR_ssh_user="vdbbench"
export PRIVATE_KEY_PATH=${private_key_path}
export PUBLIC_KEY_PATH=${public_key_path}

connect_to_vm() {
  vm_ip="$1"
  username="${TF_VAR_ssh_user}"
  ssh -o UserKnownHostsFile=/dev/null -i "${private_key_path}" "${username}@${vm_ip}"
}

format() {
    ruff check --fix .
    ruff format .
}

vdbbench() {
    python -m vdbbench $@
}
