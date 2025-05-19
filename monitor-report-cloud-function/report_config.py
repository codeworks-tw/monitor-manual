# Standard Library Imports
from constants import *
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

# Local Imports
import utils


@dataclass
class ReportConfig:
    dashboard_uid: str
    year: int = datetime.now().year
    month: int = datetime.now().month

    summary_instances: List[Dict[str, Any]] = field(default_factory=list)

    report_from: Optional[str] = None
    report_to: Optional[str] = None
    report_servergroup: str = DEFAULT_SERVERGROUP
    report_instance: str = DEFAULT_INSTANCE
    report_interval: str = DEFAULT_INTERVAL

    shutdown_instance: bool = True

    email_receivers: List[str] = None
    email_text_body: Optional[str] = None
    email_subject: Optional[str] = None
    email_template_id: str = None
    email_template_data: Optional[Dict[str, Any]] = None

    spreadsheet_id: str = None
    spreadsheet_tab_name: str = None

    @property
    def customer_name(self) -> Optional[str]:
        return self.email_template_data.get('customer_name', '') if self.email_template_data else ''

    @classmethod
    def from_request(self, request) -> 'ReportConfig':
        """Create ReportConfig from request parameters."""
        # Get request data
        request_json = request.get_json()
        if not request_json:
            request_json = {}

        # Convert year and month to integers
        try:
            year = int(request_json.get("year", datetime.now().year))
        except ValueError:
            year = datetime.now().year

        try:
            month = int(request_json.get("month", datetime.now().month))
        except ValueError:
            month = datetime.now().month

        # Get email receivers and convert to list
        email_receivers = request_json.get("email_receivers", [])
        if email_receivers:
            email_receivers = [
                email.strip() for email in email_receivers if email.strip()
            ]

        # Convert shutdown_instance to boolean
        shutdown_instance = request_json.get("shutdown_instance")
        if shutdown_instance is not None:
            if isinstance(shutdown_instance, bool):
                shutdown_instance = shutdown_instance
            else:
                shutdown_instance = shutdown_instance.lower() in ('true', '1',
                                                                  'yes')

        start_ts, end_ts = utils.get_grafana_time_range(year, month)

        email_template_data = request_json.get("email_template_data")
        if email_template_data:
            email_template_data['year'] = year
            email_template_data['month'] = month

        return self(
            dashboard_uid=request_json.get("dashboard_uid"),
            year=year,
            month=month,
            summary_instances=request_json.get('summary_instances'),
            report_from=request_json.get("report_from", str(start_ts)),
            report_to=request_json.get("report_to", str(end_ts)),
            report_servergroup=request_json.get("report_servergroup", DEFAULT_SERVERGROUP),
            report_instance=request_json.get("report_instance", DEFAULT_INSTANCE),
            report_interval=request_json.get("report_interval", DEFAULT_INTERVAL),
            shutdown_instance=shutdown_instance,
            email_receivers=email_receivers,
            email_text_body=request_json.get("email_text_body"),
            email_subject=request_json.get("email_subject"),
            email_template_id=request_json.get("email_template_id"),
            email_template_data=email_template_data,
            spreadsheet_id=request_json.get("spreadsheet_id", DEFAULT_SPREADSHEET_ID),
            spreadsheet_tab_name=request_json.get("spreadsheet_tab_name", DEFAULT_SPREADSHEET_TAB_NAME),
        )

    def validate(self) -> List[str]:
        """Validate the configuration and return list of errors."""
        errors = []

        if not self.dashboard_uid:
            errors.append("dashboard_uid is required")

        if not 1 <= self.month <= 12:
            errors.append("month must be between 1 and 12")

        if not self.summary_instances or len(self.summary_instances) == 0:
            errors.append("summary_instances cannot be empty")

        return errors
