# Standard Library Imports
from constants import *
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

# Local Imports
import utils


@dataclass
class ReportConfig:
    dashboard_uid: str
    year: int = datetime.now().year
    month: int = datetime.now().month

    report_from: Optional[str] = None
    report_to: Optional[str] = None
    report_servergroup: str = DEFAULT_SERVERGROUP
    report_instance: str = DEFAULT_INSTANCE
    report_interval: str = DEFAULT_INTERVAL

    shutdown_instance: bool = True

    email_receivers: List[str] = None
    email_text_body: Optional[str] = None
    email_subject: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None

    spreadsheet_id: str = None
    spreadsheet_tab_name: str = None

    @classmethod
    def from_request(cls, request) -> 'ReportConfig':
        """Create ReportConfig from request parameters."""
        # Get request data
        request_json = request.get_json()
        if not request_json:
            request_json = {}

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

        # Convert year and month to integers
        try:
            year = int(request_json.get("year", datetime.now().year))
        except ValueError:
            year = datetime.now().year

        try:
            month = int(request_json.get("month", datetime.now().month))
        except ValueError:
            month = datetime.now().month

        start_ts, end_ts = utils.get_grafana_time_range(year, month)
        return cls(
            dashboard_uid=request_json.get("dashboard_uid"),
            year=year,
            month=month,
            report_from=request_json.get("report_from", str(start_ts)),
            report_to=request_json.get("report_to", str(end_ts)),
            report_servergroup=request_json.get("report_servergroup",
                                                DEFAULT_SERVERGROUP),
            report_instance=request_json.get("report_instance",
                                             DEFAULT_INSTANCE),
            report_interval=request_json.get("report_interval",
                                             DEFAULT_INTERVAL),
            shutdown_instance=shutdown_instance,
            email_receivers=email_receivers,
            email_text_body=request_json.get("email_text_body"),
            email_subject=request_json.get("email_subject"),
            template_id=request_json.get("template_id"),
            template_data=request_json.get("template_data"),
            spreadsheet_id=request_json.get("spreadsheet_id"),
            spreadsheet_tab_name=request_json.get("spreadsheet_tab_name"),
        )

    def validate(self) -> List[str]:
        """Validate the configuration and return list of errors."""
        errors = []

        if not self.dashboard_uid:
            errors.append("dashboard_uid is required")

        if not 1 <= self.month <= 12:
            errors.append("month must be between 1 and 12")

        # if self.report_from and self.report_to:
        #     try:
        #         from_date = datetime.fromisoformat(self.report_from)
        #         to_date = datetime.fromisoformat(self.report_to)
        #         if to_date < from_date:
        #             errors.append(
        #                 "report_to date must be after report_from date")
        #     except ValueError:
        #         errors.append(
        #             "Invalid date format for report_from or report_to")

        return errors
