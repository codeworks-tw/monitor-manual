# Standard Library Imports
import os
from datetime import datetime

# Third-Party Library Imports
import requests
from jinja2 import Environment, FileSystemLoader
import pdfkit

# Local Imports
import utils
from compute_engine import ComputeEngineInstance
from report_config import ReportConfig
from constants import *

@utils.timer
def generate_maintenance_summary_report(config: ReportConfig):
    """Generate HTML summary report and convert it to PDF.

    Args:
        config (ReportConfig): The configuration for the report.

    Returns:
        str: Path to the generated PDF file.
    """

    dashboard_uid = config.dashboard_uid
    year = config.year
    month = config.month
    customer_name = config.customer_name
    spreadsheet_id = config.spreadsheet_id
    spreadsheet_tab_name = config.spreadsheet_tab_name
    summary_instances = config.summary_instances
    # Setup Jinja2 environment
    # Update the path to the current directory's parent directory for templates
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('maintenance_summary.html')

    (table_headers, table_data, instance_details) = utils.build_template_data(
        dashboard_uid=dashboard_uid,
        year=year,
        month=month,
        summary_instances=summary_instances,
        spreadsheet_id=spreadsheet_id,
        spreadsheet_tab_name=spreadsheet_tab_name
    )
    # Render template with data
    html_content = template.render(year=year,
                                   month=month,
                                   table_headers=table_headers,
                                   table_data=table_data,
                                   customer_name=customer_name,
                                   instance_details=instance_details
                                   )

    # Save rendered HTML to a file
    output_html_filepath = os.path.join(template_dir, 'maintenance_summary_output.html')
    with open(output_html_filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated HTML report at: {output_html_filepath}")

    # Convert HTML to PDF
    output_pdf_filename = f"{(customer_name+'-') if customer_name else ''}系統運作摘要與重點紀錄-{year}-{month:02}-{round(datetime.now().timestamp())}.pdf"

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
        pdfkit.from_file(output_html_filepath, output_pdf_filename, options=options)
        print(f"Generated PDF report at: {output_pdf_filename}")

        utils.upload_to_gcs(bucket_name=GCS_BUCKET, source_filename=output_pdf_filename,
                            destination_blob_name=f"{GCS_BASE_PATH}/{year}-{month:02}/{output_pdf_filename}")

        return output_pdf_filename

    except Exception as e:
        raise (f"Error converting HTML to PDF: {str(e)}")

@utils.timer
def generate_monitor_report(config: ReportConfig) -> str:
    dashboard_uid = config.dashboard_uid
    year = config.year
    month = config.month
    customer_name = config.customer_name
    report_from = config.report_from
    report_to = config.report_to
    report_servergroup = config.report_servergroup
    report_instance = config.report_instance
    report_interval = config.report_interval
    shutdown_instance = config.shutdown_instance

    try:
        # Create VM instance
        vm_instance = ComputeEngineInstance()
        vm_instance.create()

        # Download report
        filename = utils.download_report(dashboard_uid, report_from, report_to, report_servergroup, report_instance, report_interval,
                                         filename=f"{(customer_name + '-') if customer_name else ''}伺服器執行情況報表-{year}-{month:02}-{round(datetime.now().timestamp())}.pdf")

        # Upload to GCS for backup
        utils.upload_to_gcs(bucket_name=GCS_BUCKET, source_filename=filename, destination_blob_name=f"{GCS_BASE_PATH}/{year}-{month:02}/{filename}")

        print(f'Successfully generated report for dashboard {dashboard_uid}')
        return filename

    except requests.exceptions.RequestException as e:
        raise Exception(f"Error downloading report: {str(e)}")
    except Exception as e:
        raise Exception(f"Error generating report: {str(e)}")
    finally:
        # Delete the VM instance only if shutdown_instance is True
        if shutdown_instance:
            vm_instance.delete()
        else:
            print(f"Instance {INSTANCE_NAME} will be kept running as requested")
