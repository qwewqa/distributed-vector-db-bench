# Distributed Vector DB Bench

## Setup

### Prerequisites
Ensure the following are installed:
- Terraform
- Google Cloud (gcloud) CLI
- Python 3.10+

### Initial Setup
Create a Google Cloud project.

### Running (Linux)
Source `setup.sh`
```bash
. setup.sh <google-cloud-project-id>
```

Run the code
```bash
python -m vdbbench COMMAND [ARGS]...
```

Examples:
```bash
python -m vdbbench run test-elasticsearch
```
```bash
python -m vdbbench destroy-all
```
