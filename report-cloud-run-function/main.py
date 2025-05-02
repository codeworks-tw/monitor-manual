from google.cloud import compute_v1
from datetime import datetime
from config import INSTANCE_NAME, PROJECT, REGION, ZONE
import utils
import functions_framework
import requests
import time
import os

# Constants
DEFAULT_INTERVAL = "30s"
DEFAULT_SERVERGROUP = "All"
DEFAULT_INSTANCE = "All"
GCS_BUCKET = "cw-general"
GCS_BASE_PATH = "monitor-report"
GRAFANA_BASE_URL = "http://10.139.0.2:3000"
GRAFANA_REPORT_ENDPOINT = "/api/plugins/mahendrapaipuri-dashboardreporter-app/resources/report"

def instance_exists(instance_client):
    """Check if the VM instance exists."""
    try:
        instance_client.get(project=PROJECT, zone=ZONE, instance=INSTANCE_NAME)
        return True
    except Exception:
        return False

def create_vm_instance(instance_client):
    """Create a Compute Engine VM instance from a machine image if it doesn't exist."""
    if instance_exists(instance_client):
        print(f"Instance {INSTANCE_NAME} already exists, skipping creation.")
        return
    
    instance = compute_v1.Instance()
    instance.name = INSTANCE_NAME
    instance.source_machine_image = f"projects/{PROJECT}/global/machineImages/monitor-report-renderer"
    instance.network_interfaces = [compute_v1.NetworkInterface(
        name=f"projects/{PROJECT}/global/networks/cw-default",
        subnetwork=f"projects/{PROJECT}/regions/{REGION}/subnetworks/sub-default",
        network_i_p="10.139.0.3"
    )]
    operation = instance_client.insert(project=PROJECT, zone=ZONE, instance_resource=instance)
    operation.result()

def delete_vm_instance(instance_client):
    """Delete the VM instance."""
    delete_op = instance_client.delete(project=PROJECT, zone=ZONE, instance=INSTANCE_NAME)
    delete_op.result()

def download_report(dashboard_uid, report_from, report_to, report_servergroup, 
                   report_instance, report_interval, grafana_token):
    """Download the report from Grafana."""
    headers = {"Authorization": f"Bearer {grafana_token}"}
    report_url = (
        f"{GRAFANA_BASE_URL}{GRAFANA_REPORT_ENDPOINT}"
        f"?dashUid={dashboard_uid}"
        f"&from={report_from}"
        f"&to={report_to}"
        f"&var-servergroup={report_servergroup}"
        f"&var-instance={report_instance}"
        f"&var-interval={report_interval}"
    )
    response = requests.get(report_url, headers=headers)
    response.raise_for_status()
    
    file_name = f"report-{dashboard_uid}-from-{report_from}-to-{report_to}-{int(time.time())}.pdf"
    with open(file_name, "wb") as f:
        f.write(response.content)
    return file_name

@functions_framework.http
def generate_report(request):
    """Generate a report from Grafana dashboard and send it via email."""
    try:
        # Get and validate required parameters
        dashboard_uid = request.args.get("dashboard_uid")
        if not dashboard_uid:
            return "Error: dashboard_uid is required", 400

        report_from = request.args.get("report_from")
        if not report_from:
            return "Error: report_from is required", 400

        report_to = request.args.get("report_to")
        if not report_to:
            return "Error: report_to is required", 400

        # Get optional parameters with defaults
        report_servergroup = request.args.get("report_servergroup", DEFAULT_SERVERGROUP)
        report_instance = request.args.get("report_instance", DEFAULT_INSTANCE)
        report_interval = request.args.get("report_interval", DEFAULT_INTERVAL)
        
        # Get storage and email parameters
        storage_folder = request.args.get("storage_folder", datetime.now().strftime("%Y-%m"))
        email_receivers = request.args.get("email_receivers", "")
        email_text_body = request.args.get("email_text_body", "Monthly Monitor Report is ready.")
        email_subject = request.args.get("email_subject", "Monthly Monitor Report")
        
        # Get Grafana token
        grafana_token = utils.get_secret_value("grafana-service-account-token")
        
        # Create VM instance
        instance_client = compute_v1.InstancesClient()
        create_vm_instance(instance_client)
        
        try:
            # Download report
            file_name = download_report(
                dashboard_uid, report_from, report_to, 
                report_servergroup, report_instance, 
                report_interval, grafana_token
            )
            
            # Upload to GCS
            utils.upload_to_gcs(
                bucket_name=GCS_BUCKET,
                source_file_name=file_name,
                destination_blob_name=f"{GCS_BASE_PATH}/{storage_folder}/{file_name}"
            )
            
            # Send email if receivers are specified
            if email_receivers:
                receivers = [email.strip() for email in email_receivers.split(",") if email.strip()]
                if receivers:
                    email_file_name = request.args.get("email_file_name", file_name)
                    utils.send_email(
                        file_path=file_name,
                        file_name=email_file_name,
                        email_receivers=receivers,
                        email_subject=email_subject,
                        email_text_body=email_text_body
                    )
            
            return f'Successfully generated report for dashboard {dashboard_uid}'
            
        finally:
            # Always delete the VM instance
            delete_vm_instance(instance_client)
            
    except requests.exceptions.RequestException as e:
        return f"Error downloading report: {str(e)}", 500
    except Exception as e:
        return f"Error generating report: {str(e)}", 500