# Standard Library Imports
import os
from datetime import datetime

# Third-Party Library Imports
import requests
import functions_framework
from google.cloud import compute_v1
from jinja2 import Environment, FileSystemLoader
import pdfkit

# Local Imports
import utils
from compute_engine import ComputeEngineInstance
from report_config import ReportConfig
from constants import *


@functions_framework.http
def main(request):
    """HTTP Cloud Function to generate and send monitor reports.
    
    Args:
        request (flask.Request): The request object.
        
    Returns:
        tuple: (response_text, status_code)
    """
    try:

        # Parse and validate request parameters
        config = ReportConfig.from_request(request)
        errors = config.validate()
        print('request config: ', config)

        if errors:
            return {'error': 'Invalid parameters', 'details': errors}, 400

        # Generate reports
        html_summary_report = generate_html_summary_report(
            dashboard_uid=config.dashboard_uid,
            year=config.year,
            month=config.month,
            spreadsheet_id=config.spreadsheet_id,
            spreadsheet_tab_name=config.spreadsheet_tab_name)

        monitor_report = generate_report(
            dashboard_uid=config.dashboard_uid,
            year=config.year,
            month=config.month,
            report_from=config.report_from,
            report_to=config.report_to,
            report_servergroup=config.report_servergroup,
            report_instance=config.report_instance,
            report_interval=config.report_interval,
            shutdown_instance=config.shutdown_instance)

        # # Send email if receivers are specified
        if config.email_receivers:
            utils.send_email(file_paths=[html_summary_report, monitor_report],
                             email_receivers=config.email_receivers,
                             email_text_body=config.email_text_body,
                             email_subject=config.email_subject,
                             template_id=config.template_id,
                             template_data=config.template_data)

        return {
            'status': 'success',
            'message': 'Report generated and sent successfully'
        }, 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'error': str(e)}, 500


def generate_html_summary_report(dashboard_uid: str, year: int, month: int,
                                 spreadsheet_id: str,
                                 spreadsheet_tab_name: str):
    """Generate HTML summary report and convert it to PDF.
    
    Args:
        year (int): Year for the report.
        month (int): Month for the report.
        
    Returns:
        tuple: (html_file_path, pdf_file_path) Paths to the generated HTML and PDF files.
    """
    # Setup Jinja2 environment
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('template.html')

    (table_headers, table_data, total_upload_size, total_download_size,
     alert_count,
     availability_rate) = utils.build_template_data(dashboard_uid, year, month,
                                                    spreadsheet_id,
                                                    spreadsheet_tab_name)

    # Render template with data
    html_content = template.render(year=year,
                                   month=month,
                                   table_headers=table_headers,
                                   table_data=table_data,
                                   total_upload_size=total_upload_size,
                                   total_download_size=total_download_size,
                                   alert_count=alert_count,
                                   availability_rate=availability_rate)

    # Save rendered HTML to a file
    output_html = os.path.join(template_dir, 'output.html')
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated HTML report at: {output_html}")

    # Convert HTML to PDF
    output_pdf = os.path.join(template_dir, '系統運作摘要與重點紀錄.pdf')
    try:
        # Configure pdfkit options
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'quiet': ''
        }

        # Convert HTML to PDF
        pdfkit.from_file(output_html, output_pdf, options=options)
        print(f"Generated PDF report at: {output_pdf}")

        return output_pdf

    except Exception as e:
        print(f"Error converting HTML to PDF: {str(e)}")
        return None


def generate_report(
    dashboard_uid: str,
    year: int,
    month: int,
    report_from: str,
    report_to: str,
    report_servergroup: str = DEFAULT_SERVERGROUP,
    report_instance: str = DEFAULT_INSTANCE,
    report_interval: str = DEFAULT_INTERVAL,
    shutdown_instance: bool = True,
    storage_folder: str = datetime.now().strftime("%Y-%m")
) -> str:
    try:
        # Create VM instance
        instance_client = compute_v1.InstancesClient()
        vm_instance = ComputeEngineInstance(instance_client)
        vm_instance.create()

        try:
            # Download report

            file_name = utils.download_report(
                dashboard_uid,
                report_from,
                report_to,
                report_servergroup,
                report_instance,
                report_interval,
                file_name=
                f"伺服器執行情況報表-{year}-{month}-{round(datetime.now().timestamp(), 0)}.pdf"
            )

            # Upload to GCS for backup
            utils.upload_to_gcs(
                bucket_name=GCS_BUCKET,
                source_file_name=file_name,
                destination_blob_name=
                f"{GCS_BASE_PATH}/{storage_folder}/{file_name}")

            print(
                f'Successfully generated report for dashboard {dashboard_uid}')
            return file_name

        finally:
            # Delete the VM instance only if shutdown_instance is True
            if shutdown_instance:
                vm_instance.delete()
            else:
                print(
                    f"Instance {INSTANCE_NAME} will be kept running as requested"
                )

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading report: {str(e)}")
    except Exception as e:
        raise Exception(f"Error generating report: {str(e)}")
