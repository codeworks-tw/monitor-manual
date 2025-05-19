# Standard Library Imports
import os
import base64
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, Callable

# Third-Party Library Imports
import requests
from google.cloud import storage, secretmanager
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Local Imports
from constants import *
from report_config import ReportConfig


def timer(func: Callable) -> Callable:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Time taken by {func.__name__}: {end - start:.4f} seconds")
        return result
    return wrapper


def get_secret_value(secret_id: str, version_id: str = "latest"):
    """
    Retrieves a secret value from Google Cloud Platform Secret Manager.

    Args:
        secret_id (str): The name/ID of the secret to retrieve
        version_id (str, optional): The version of the secret. Defaults to "latest"

    Returns:
        str: The decoded secret value, or empty string if not found
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    token = response.payload.data.decode("UTF-8")
    return token or ""


GRAFANA_TOKEN = get_secret_value("grafana-service-account-token")


def upload_to_gcs(
        bucket_name: str,
        source_filename: str,
        destination_blob_name: str):
    """
    Uploads a local file to Google Cloud Storage bucket.

    Args:
        bucket_name (str): The name of the GCS bucket (e.g., 'cw-general')
        source_filename (str): Path to the local file to upload
        destination_blob_name (str): Destination path in the GCS bucket (e.g., 'monitor-report/report.pdf')

    Prints:
        Success message with upload details
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_filename)
    print(f"✅ File {source_filename} uploaded to gs://{bucket_name}/{destination_blob_name}.")


def query_prometheus(query: str, time: float):
    if not query:
        return None

    request_url = (f"{PROMETHEUS_BASE_URL}/api/v1/query"
                   f"?query={query}"
                   f"&time={time}")
    response = requests.get(request_url)
    result = response.json()
    response.raise_for_status()
    return result


def get_grafana_annotations(dashboardUID: str = 'cel9ij7o23ev4a', type: str = 'alert'):
    headers = {"Authorization": f"Bearer {GRAFANA_TOKEN}"}
    request_url = (f"{GRAFANA_BASE_URL}/api/annotations"
                   f"?type={type}"
                   f"&dashboardUID={dashboardUID}")
    response = requests.get(request_url, headers=headers)
    response.raise_for_status()
    result = response.json()
    response.raise_for_status()
    return result


def get_spreadsheet_tab_rows(spreadsheet_id: str, spreadsheet_tab_name: str):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    try:
        # Get credentials from service account
        service_account_json = json.loads(get_secret_value("30508068041-compute-service-account"))
        credentials = service_account.Credentials.from_service_account_info(service_account_json, scopes=SCOPES)

        # Initialize Sheets API
        sheets_service = build('sheets', 'v4', credentials=credentials)

        # Get the values from the specified tab
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f'{spreadsheet_tab_name}!A:Z'  # get all columns from A to Z
        ).execute()

        values = result.get('values', [])

        if not values:
            return {
                'status': 'error',
                'message': f'No data found in tab "{spreadsheet_tab_name}"'
            }, 404

        header_row = values[0]  # First row as headers
        data_rows = values[1:]  # Rest of the data

        aligned_data_rows = []

        # Iterate over each row in the data
        for row in data_rows:
            # Create a dictionary to map the data to the headers
            row_dict = {
                header: '' for header in header_row  # Initialize with empty strings
            }
            # Fill in the data for the columns that exist
            for i, value in enumerate(row):
                if i < len(header_row):  # Ensure we don't exceed the number of headers
                    row_dict[header_row[i]] = value
            # Append the aligned row to the list
            aligned_data_rows.append([row_dict[header] for header in header_row])

        return header_row, aligned_data_rows

    except Exception as e:
        raise Exception(f"Exception occurred while processing data: {str(e)}")


def extract_query_single_value(query_result):
    """Extract value from Prometheus query result"""
    try:
        if query_result:
            result_val = query_result \
                .get('data', {}) \
                .get('result', [{}])[0] \
                .get('value', [None, None])[1]

            if result_val:
                return result_val
    except (KeyError, IndexError):
        raise Exception('Error while extracting Prometheus query result')
    return None


def get_first_day_timestamp_of_next_month(
        year: int,
        month: int,
        tz: timezone = UTC_PLUS_8) -> datetime:
    d = datetime(year, month, 1, 0, 0, 0, tzinfo=tz)
    if month == 12:
        d = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=tz)
    else:
        d = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=tz)
    return d


def get_grafana_time_range(
        year: int,
        month: int,
        tz: timezone = UTC_PLUS_8):
    # Start of the current month at 00:00:00
    start_dt = datetime(year, month, 1, tzinfo=tz)

    # Start of next month
    if month == 12:
        next_month_dt = datetime(year + 1, 1, 1, tzinfo=tz)
    else:
        next_month_dt = datetime(year, month + 1, 1, tzinfo=tz)

    # Convert to epoch milliseconds
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(next_month_dt.timestamp() * 1000)

    return start_ts, end_ts


def build_template_data(
        dashboard_uid: str,
        year: int,
        month: int,
        summary_instances: list[dict],
        spreadsheet_id: str,
        spreadsheet_tab_name: str):

    header_row, data_rows = get_spreadsheet_tab_rows(spreadsheet_id, spreadsheet_tab_name)
    table_headers = header_row[:2] + header_row[4:]
    table_data = [row[:2] + row[4:] for row in data_rows]
    instance_details = []

    # Get timestamp of the first day of the next month as query time
    timestamp = round(
        get_first_day_timestamp_of_next_month(year, month).timestamp(), 0)

    # Filtered history alerts whose new state is Alerting and convert json details from text, then get number of alerts per instance
    alerts = get_grafana_annotations(dashboard_uid)
    fired_alerts_details = [alert for alert in alerts if alert["newState"] == GRAFANA_ALERTING_STATE_ALERTING]

    for alert in fired_alerts_details:
        jsonDetails = extract_json_from_text(alert["text"])
        alert["details"] = jsonDetails

    for instance in summary_instances:
        details = get_instance_details(instance, timestamp)

        # nodata errors that text content does not contain instance info will be filtered out
        details["alert_count"] = len([
            alert for alert in fired_alerts_details
            if alert.get("details", {}).get("instance") == instance["source"]
        ])

        instance_details.append(details)

    return table_headers, table_data, instance_details


def get_instance_details(instance, timestamp) -> dict[str, Any]:
    if not instance['source']:
        return None

    total_upload_size = "0 GB"
    total_download_size = "0 GB"
    availability_rate = 100

    total_upload_result = query_prometheus(
        query=f"sum(increase(node_network_transmit_bytes_total{{instance='{instance['source']}'}}[30d])) by (instance)",
        time=timestamp)
    total_download_result = query_prometheus(
        query=f"sum(increase(node_network_receive_bytes_total{{instance='{instance['source']}'}}[30d])) by (instance)",
        time=timestamp)
    availability_rate_result = query_prometheus(
        query=f"avg_over_time(up{{job='node-status', instance='{instance['source']}'}}[30d]) * 100",
        time=timestamp)

    # Calculate total upload size and round to 2 decimal places
    if upload_val := extract_query_single_value(total_upload_result):
        upload_gb = float(upload_val) / (1024**3)
        total_upload_size = f'{upload_gb:.3f} GB'

    # Calculate total download size and round to 2 decimal places
    if download_val := extract_query_single_value(total_download_result):
        download_gb = float(download_val) / (1024**3)
        total_download_size = f'{download_gb:.3f} GB'

    # Calculate availability rate and round to 2 decimal places, if the value is greater than 90% it's set to 100%
    if availability_rate_val := extract_query_single_value(availability_rate_result):
        availability_rate = 100 if float(availability_rate_val) > 90 \
            else round(float(availability_rate_val), 2)

    # Calculate alert count by filtering alerts where the state is 'Alerting'
    # alerts = get_grafana_annotations(dashboard_uid)
    # alert_count = len([alert for alert in alerts if alert.get('newState') == 'Alerting'])

    return {
        **instance,
        "total_upload_size": total_upload_size,
        "total_download_size": total_download_size,
        "availability_rate": availability_rate
    }


def extract_json_from_text(text: str) -> dict[str, str]:
    match = re.search(r"\{(.+?)\}", text)
    if not match:
        return None

    kv_string = match.group(1)
    try:
        return {
            key.strip(): value.strip()
            for key, value in (pair.split("=", 1) for pair in kv_string.split(", "))
        }
    except ValueError:
        return None  # Handle malformed input gracefully


def download_report(
        dashboard_uid,
        report_from,
        report_to,
        report_servergroup,
        report_instance,
        report_interval,
        filename):
    """Download the report from Grafana."""
    headers = {"Authorization": f"Bearer {GRAFANA_TOKEN}"}
    report_url = (f"{GRAFANA_BASE_URL}{GRAFANA_REPORT_ENDPOINT}"
                  f"?dashUid={dashboard_uid}"
                  f"&from={report_from}"
                  f"&to={report_to}"
                  f"&var-servergroup={report_servergroup}"
                  f"&var-instance={report_instance}"
                  f"&var-interval={report_interval}")
    response = requests.get(report_url, headers=headers)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)
    return filename


def send_email(config: ReportConfig, attachment_paths=None):
    """Send an email with optional attachments using SMTP2Go API.

    Args:
        attachment_paths (list[str] or str, optional): Path(s) to the local file(s) to be attached
        receivers (list[str]): List of email addresses
        subject (str, optional): Email subject. Defaults to "Monthly Monitor Report"
        text_body (str, optional): Email body text. Defaults to "Monthly Monitor Report is ready."
        template_id (str, optional): Template ID for template-based emails
        template_data (dict, optional): Data to be used in the template
    """
    receivers = config.email_receivers
    text_body = config.email_text_body
    subject = config.email_subject
    template_id = config.email_template_id
    template_data = config.email_template_data

    payload = {
        "sender": "report@codeworkstw.com",
        "to": receivers,
    }

    # Add template data if provided, otherwise add regular email data
    if template_id:
        payload["template_id"] = template_id
        if template_data:
            payload["template_data"] = template_data
    else:
        payload.update({
            "subject": subject,
            "text_body": text_body,
        })

    # Add attachment(s) if attachment_paths is provided
    if attachment_paths:
        # Convert single file to list for consistent handling
        if isinstance(attachment_paths, str):
            attachment_paths = [attachment_paths]

        attachments = []

        for path in attachment_paths:
            with open(path, "rb") as f:
                encoded_file = base64.b64encode(f.read()).decode("utf-8")
            # Use the filename from the path
            filename = os.path.basename(path)
            attachments.append({
                "filename": filename,
                "fileblob": encoded_file
            })
        payload["attachments"] = attachments

    response = requests.post(
        "https://api.smtp2go.com/v3/email/send",
        headers={
            "X-Smtp2go-Api-Key":
            get_secret_value("smtp2go-api-key"),
            "Content-Type":
            "application/json"
        },
        json=payload
    )
    response.raise_for_status()
