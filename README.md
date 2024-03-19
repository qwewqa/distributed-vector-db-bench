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
# Test elasticsearch
python -m vdbbench run elasticsearch-test
```
```bash
# Benchmark elasticsearch query performance on fashion-mnist
python -m vdbbench run elasticsearch-query dataset=\"fashion-mnist\"
```
```bash
# Benchmark elasticsearch query with the elasticsearch_query_mnist.json config
python -m vdbbench run --config configs/elasticsearch_query_mnist.json
```
```bash
# Benchmark elasticsearch query with the elasticsearch_query_mnist.json config, overriding data.dataset
python -m vdbbench run --config configs/elasticsearch_query_mnist.json data.dataset=\"glove-25d\"
```
```bash
# Destroy all terraform resources
python -m vdbbench destroy-all
```
