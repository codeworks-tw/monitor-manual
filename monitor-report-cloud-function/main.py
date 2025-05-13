# Third-Party Library Imports
import functions_framework

# Local Imports
import utils
from report_config import ReportConfig
from report_generator import generate_maintenance_summary_report, generate_monitor_report
from constants import *

env_path = './.env'
if os.getenv('ENVIRONMENT') == 'prod':
    env_path = './.prod.env'
print('Load Environment Path:', env_path)
# Load the specific environment file
load_dotenv(dotenv_path=env_path)


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

        if errors:
            return {'error': 'Invalid parameters', 'details': errors}, 400

        # Generate reports
        maintenance_summary_report = generate_maintenance_summary_report(config)
        monitor_report = generate_monitor_report(config)

        print(maintenance_summary_report, monitor_report)
        # Send email if receivers are specified
        if config.email_receivers:
            utils.send_email(
                config=config,
                attachment_paths=[maintenance_summary_report, monitor_report]
            )

        return {
            'status': 'success',
            'message': 'Report generated and sent successfully'
        }, 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'error': str(e)}, 500


# def generate_maintenance_summary_report(config: ReportConfig):
#     """Generate HTML summary report and convert it to PDF.

#     Args:
#         year (int): Year for the report.
#         month (int): Month for the report.

#     Returns:
#         tuple: (html_file_path, pdf_file_path) Paths to the generated HTML and PDF files.
#     """

#     dashboard_uid = config.dashboard_uid,
#     year = config.year,
#     month = config.month,
#     customer_name = config.customer_name,
#     spreadsheet_id = config.spreadsheet_id,
#     spreadsheet_tab_name = config.spreadsheet_tab_name

#     # Setup Jinja2 environment
#     template_dir = os.path.dirname(os.path.abspath(__file__))
#     env = Environment(loader=FileSystemLoader(template_dir))
#     template = env.get_template('template.html')

#     (table_headers, table_data, total_upload_size, total_download_size,
#      alert_count,
#      availability_rate) = utils.build_template_data(dashboard_uid, year, month,
#                                                     spreadsheet_id,
#                                                     spreadsheet_tab_name)

#     # Render template with data
#     html_content = template.render(year=year,
#                                    month=month,
#                                    table_headers=table_headers,
#                                    table_data=table_data,
#                                    total_upload_size=total_upload_size,
#                                    total_download_size=total_download_size,
#                                    alert_count=alert_count,
#                                    availability_rate=availability_rate)

#     # Save rendered HTML to a file
#     output_html_filepath = os.path.join(template_dir, 'output.html')
#     with open(output_html_filepath, 'w', encoding='utf-8') as f:
#         f.write(html_content)

#     print(f"Generated HTML report at: {output_html_filepath}")

#     # Convert HTML to PDF
#     output_pdf_filename = f"{(customer_name+'-') if customer_name else ''}系統運作摘要與重點紀錄-{year}-{month:02}-{round(datetime.now().timestamp())}.pdf"

#     try:
#         # Configure pdfkit options
#         options = {
#             'page-size': 'A4',
#             'margin-top': '0.75in',
#             'margin-right': '0.75in',
#             'margin-bottom': '0.75in',
#             'margin-left': '0.75in',
#             'encoding': 'UTF-8',
#             'no-outline': None,
#             'quiet': ''
#         }

#         # Convert HTML to PDF
#         pdfkit.from_file(output_html_filepath,
#                          output_pdf_filename,
#                          options=options)
#         print(f"Generated PDF report at: {output_pdf_filename}")

#         utils.upload_to_gcs(
#             bucket_name=GCS_BUCKET,
#             source_filename=output_pdf_filename,
#             destination_blob_name=f"{GCS_BASE_PATH}/{year}-{month:02}/{output_pdf_filename}")

#         return output_pdf_filename

#     except Exception as e:
#         print(f"Error converting HTML to PDF: {str(e)}")
#         return None


# def generate_monitor_report(config: ReportConfig) -> str:
#     dashboard_uid = config.dashboard_uid,
#     year = config.year,
#     month = config.month,
#     customer_name = config.customer_name,
#     report_from = config.report_from,
#     report_to = config.report_to,
#     report_servergroup = config.report_servergroup,
#     report_instance = config.report_instance,
#     report_interval = config.report_interval,
#     shutdown_instance = config.shutdown_instance

#     try:
#         # Create VM instance
#         vm_instance = ComputeEngineInstance()
#         vm_instance.create()

#         # Download report
#         filename = utils.download_report(
#             dashboard_uid,
#             report_from,
#             report_to,
#             report_servergroup,
#             report_instance,
#             report_interval,
#             filename=f"{(customer_name + '-') if customer_name else ''}伺服器執行情況報表-{year}-{month:02}-{round(datetime.now().timestamp())}.pdf"
#         )

#         # Upload to GCS for backup
#         utils.upload_to_gcs(bucket_name=GCS_BUCKET,
#                             source_filename=filename,
#                             destination_blob_name=f"{GCS_BASE_PATH}/{year}-{month:02}/{filename}")

#         print(f'Successfully generated report for dashboard {dashboard_uid}')
#         return filename

#     except requests.exceptions.RequestException as e:
#         raise Exception(f"Error downloading report: {str(e)}")
#     except Exception as e:
#         raise Exception(f"Error generating report: {str(e)}")
#     finally:
#         # Delete the VM instance only if shutdown_instance is True
#         if shutdown_instance:
#             vm_instance.delete()
#         else:
#             print(f"Instance {INSTANCE_NAME} will be kept running as requested")
