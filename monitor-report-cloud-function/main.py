# Standard Library Imports
import json
import tempfile
import time
from datetime import datetime

# Third-Party Library Imports
import pandas as pd
import requests
import functions_framework
from google.cloud import compute_v1, storage
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Local Imports
import utils
from config import INSTANCE_NAME, PROJECT, REGION, ZONE

# Constants
DEFAULT_INTERVAL = "30s"
DEFAULT_SERVERGROUP = "All"
DEFAULT_INSTANCE = "All"
GCS_BUCKET = "cw-general"
GCS_BASE_PATH = "monitor-report"
GRAFANA_BASE_URL = "http://10.139.0.2:3000"
GRAFANA_REPORT_ENDPOINT = "/api/plugins/mahendrapaipuri-dashboardreporter-app/resources/report"

# Initialize the Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

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
    
    file_name = f"report-{dashboard_uid}-{int(time.time())}.pdf"
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
        shutdown_instance = request.args.get("shutdown_instance", "true").lower() == "true"
        
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
            # Delete the VM instance only if shutdown_instance is True
            if shutdown_instance:
                delete_vm_instance(instance_client)
            else:
                print(f"Instance {INSTANCE_NAME} will be kept running as requested")
            
    except requests.exceptions.RequestException as e:
        return f"Error downloading report: {str(e)}", 500
    except Exception as e:
        return f"Error generating report: {str(e)}", 500

@functions_framework.http
def get_spreadsheet_tab(request):
    try:
        # Get parameters from request
        spreadsheet_id = request.args.get('spreadsheet_id')
        tab_name = request.args.get('tab_name')
        file_format = request.args.get('format', 'csv')  # Default to CSV
        storage_folder = request.args.get('storage_folder', datetime.now().strftime("%Y-%m"))
        
        if not spreadsheet_id:
            return 'No spreadsheet_id provided', 400
        if not tab_name:
            return 'No tab_name provided', 400
            
        # Get credentials from service account
        service_account_json = json.loads(utils.get_secret_value("30508068041-compute-service-account"))
        credentials = service_account.Credentials.from_service_account_info(
            service_account_json, scopes=SCOPES)
            
        # Initialize Sheets API
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        # Get the values from the specified tab
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{tab_name}!A:Z'  # This will get all columns from A to Z
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            return {
                'status': 'error',
                'message': f'No data found in tab "{tab_name}"'
            }, 404
            
        # Get the headers and data
        headers = values[0]  # First row as headers
        data = values[1:]    # Rest of the data

        # Create a list to store the aligned data
        aligned_data = []

        # Iterate over each row in the data
        for row in data:
            # Create a dictionary to map the data to the headers
            row_dict = {header: '' for header in headers}  # Initialize with empty strings
            
            # Fill in the data for the columns that exist
            for i, value in enumerate(row):
                if i < len(headers):  # Ensure we don't exceed the number of headers
                    row_dict[headers[i]] = value
            
            # Append the aligned row to the list
            aligned_data.append([row_dict[header] for header in headers])

        # Create the DataFrame
        df = pd.DataFrame(aligned_data, columns=headers)
        
        # Create a temporary file based on the requested format
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}') as temp_file:
            if file_format.lower() == 'csv':
                df.to_csv(temp_file.name, index=False)
            elif file_format.lower() == 'xlsx':
                df.to_excel(temp_file.name, index=False)
            else:
                return {
                    'status': 'error',
                    'message': f'Unsupported file format: {file_format}',
                    'supported_formats': ['csv', 'xlsx']
                }, 400
            
            # Upload to GCS
            file_name = f'tab-{tab_name}-{int(time.time())}.{file_format}'
            utils.upload_to_gcs(
                bucket_name=GCS_BUCKET,
                source_file_name=temp_file.name,
                destination_blob_name=f"{GCS_BASE_PATH}/{storage_folder}/{file_name}"
            )
            
            return {
                'status': 'success',
                'file_name': file_name,
                'bucket': GCS_BUCKET,
                'blob_name': f"{GCS_BASE_PATH}/{storage_folder}/{file_name}",
                'format': file_format,
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500