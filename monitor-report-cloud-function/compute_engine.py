"""Google Compute Engine instance management module.

This module provides a class for managing Google Compute Engine VM instances,
including creation, deletion, and existence checks.
"""
# Standard Library Imports
from dataclasses import dataclass
from google.cloud import compute_v1

# Local Imports
from constants import *


@dataclass
class ComputeEngineInstance:
    """A class to manage Google Compute Engine VM instances.

    This class provides methods for creating, deleting, and checking the existence
    of VM instances in Google Compute Engine.

    Attributes:
        instance_client: The Compute Engine instance client.
    """

    def __init__(self):
        self.instance_client = compute_v1.InstancesClient()

    def exists(self) -> bool:
        """Check if the VM instance exists.

        Returns:
            bool: True if the instance exists, False otherwise.
        """
        try:
            self.instance_client.get(project=PROJECT,
                                     zone=ZONE,
                                     instance=INSTANCE_NAME)
            return True
        except Exception:
            return False

    def create(self) -> None:
        """Create a Compute Engine VM instance from a machine image if it doesn't exist."""
        if self.exists():
            print(
                f"Instance {INSTANCE_NAME} already exists, skipping creation.")
            return

        instance = compute_v1.Instance()
        instance.name = INSTANCE_NAME
        instance.source_machine_image = f"projects/{PROJECT}/global/machineImages/monitor-report-renderer"
        instance.network_interfaces = [
            compute_v1.NetworkInterface(
                name=f"projects/{PROJECT}/global/networks/cw-default",
                subnetwork=f"projects/{PROJECT}/regions/{REGION}/subnetworks/sub-default",
                network_i_p="10.139.0.3")
        ]
        operation = self.instance_client.insert(project=PROJECT,
                                                zone=ZONE,
                                                instance_resource=instance)
        operation.result()

    def delete(self) -> None:
        """Delete the VM instance."""
        delete_op = self.instance_client.delete(project=PROJECT,
                                                zone=ZONE,
                                                instance=INSTANCE_NAME)
        delete_op.result()
