import enum
import json
from pathlib import Path
import logging
import subprocess

logger = logging.getLogger(__name__)


TERRAFORM_BASE_DIR = Path(__file__).parent / "terraform"


class DatabaseDeployment(str, enum.Enum):
    ELASTICSEARCH = "elasticsearch"


def init_terraform(db: DatabaseDeployment):
    if (TERRAFORM_BASE_DIR / db / ".terraform").exists():
        return
    logger.info(f"Initializing {db.name} module")
    module_dir = TERRAFORM_BASE_DIR / db
    subprocess.run(["terraform", "init"], cwd=module_dir)


def apply_terraform(db: DatabaseDeployment, destroy_existing: bool = False) -> dict:
    init_terraform(db)
    if destroy_existing:
        destroy_terraform(db)
    logger.info(f"Applying {db.name} module")
    subprocess.run(
        ["terraform", "apply", "-auto-approve", "-json"],
        cwd=TERRAFORM_BASE_DIR / db,
    )
    output_json = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=TERRAFORM_BASE_DIR / db,
        capture_output=True,
    ).stdout
    output_data = json.loads(output_json)
    output_data = {k: v["value"] for k, v in output_data.items()}
    return output_data


def destroy_terraform(db: DatabaseDeployment):
    init_terraform(db)
    logger.info(f"Destroying {db.name} module")
    module_dir = TERRAFORM_BASE_DIR / db
    subprocess.run(["terraform", "destroy", "-auto-approve"], cwd=module_dir)


def destroy_all_terraform():
    for db in DatabaseDeployment:
        destroy_terraform(db)
