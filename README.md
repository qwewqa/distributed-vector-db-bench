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
To see all actions
```bash
 python -m vdbbench --help
```

Examples:
```bash
python -m vdbbench run elasticsearch-test
```
```bash
python -m vdbbench destroy-all
```
