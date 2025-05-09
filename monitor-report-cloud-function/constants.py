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
DEFAULT_SPREADSHEET_TAB_NAME = "維運紀錄"

# External Service URLs

# PROMETHEUS_BASE_URL = "http://35.229.168.187:9090"
# GRAFANA_BASE_URL = "http://35.229.168.187:3000"

PROMETHEUS_BASE_URL = "http://10.139.0.2:9090"
GRAFANA_BASE_URL = "http://10.139.0.2:3000"
GRAFANA_REPORT_ENDPOINT = "/api/plugins/mahendrapaipuri-dashboardreporter-app/resources/report"

UTC_PLUS_8 = timezone(timedelta(hours=8))
