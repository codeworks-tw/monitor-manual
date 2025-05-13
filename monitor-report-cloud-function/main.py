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
