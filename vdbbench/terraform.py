import enum
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


TERRAFORM_BASE_DIR = Path(__file__).parent / "terraform"


class DatabaseDeployment(str, enum.Enum):
    """An enumeration of supported database deployments.

    The values of this enumeration are the names of the Terraform module folders in the `terraform` directory.
    """

    ELASTICSEARCH = "elasticsearch"


def init_terraform(db: DatabaseDeployment):
    """Initializes the Terraform module for the given database deployment if it has not been initialized already.

    Args:
        db: The database deployment to initialize.
    """
    if (TERRAFORM_BASE_DIR / db / ".terraform").exists():
        return
    logger.info(f"Initializing {db.name} module")
    module_dir = TERRAFORM_BASE_DIR / db
    subprocess.run(["terraform", "init"], cwd=module_dir, check=False)


def apply_terraform(db: DatabaseDeployment, destroy_existing: bool = False) -> dict:
    """Applies the Terraform module for the given database deployment.

    Args:
        db: The database deployment to apply.
        destroy_existing: Whether to destroy the existing deployment before applying the new one.

    Returns:
        A dictionary containing the output values of the Terraform module.

    """
    init_terraform(db)
    if destroy_existing:
        destroy_terraform(db)
    logger.info(f"Applying {db.name} module")
    subprocess.run(
        ["terraform", "apply", "-auto-approve", "-json"],
        cwd=TERRAFORM_BASE_DIR / db,
        check=False,
    )
    output_json = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=TERRAFORM_BASE_DIR / db,
        capture_output=True,
        check=False,
    ).stdout
    output_data = json.loads(output_json)
    output_data = {k: v["value"] for k, v in output_data.items()}
    return output_data


def destroy_terraform(db: DatabaseDeployment):
    """Destroys the Terraform module for the given database deployment.

    Args:
        db: The database deployment to destroy.

    """
    init_terraform(db)
    logger.info(f"Destroying {db.name} module")
    module_dir = TERRAFORM_BASE_DIR / db
    subprocess.run(
        ["terraform", "destroy", "-auto-approve"], cwd=module_dir, check=False
    )


def destroy_all_terraform():
    """Destroys all Terraform modules."""
    for db in DatabaseDeployment:
        destroy_terraform(db)
