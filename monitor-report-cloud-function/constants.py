import os
from datetime import timezone, timedelta

# VM Instance Configuration
INSTANCE_NAME = "monitor-report-renderer-temp"

# Google Cloud Project Configuration
PROJECT = "codeworks-457009"
REGION = "asia-east1"
ZONE = "asia-east1-c"

# Report Configuration
DEFAULT_INTERVAL = "30s"
DEFAULT_SERVERGROUP = "All"
DEFAULT_INSTANCE = "All"
GCS_BUCKET = "cw-general"
GCS_BASE_PATH = "monitor-report"

DEFAULT_SPREADSHEET_ID = "1hsXE2yT9YHvEfnadTAgi7tZHvkTXlRfek-VuEvxmhb4"
DEFAULT_SPREADSHEET_TAB_NAME_BASE = "維運紀錄"

# External Service URLs
PROMETHEUS_BASE_URL = os.getenv('PROMETHEUS_BASE_URL')
GRAFANA_BASE_URL = os.getenv('GRAFANA_BASE_URL')

GRAFANA_REPORT_ENDPOINT = "/api/plugins/mahendrapaipuri-dashboardreporter-app/resources/report"

GRAFANA_ALERTING_STATE_ALERTING = "Alerting"

UTC_PLUS_8 = timezone(timedelta(hours=8))
