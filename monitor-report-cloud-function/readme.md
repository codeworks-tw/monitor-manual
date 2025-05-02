# Monitor Report Cloud Function API Documentation

This cloud function generates reports from Grafana dashboards and can optionally send them via email. It manages a temporary VM instance for rendering the reports.



### Basic usage to save report to `Google Cloud Storage`

```
GET https://monitor-report-30508068041.asia-east1.run.app?
    dashboard_uid=abc123&
    report_from=now-30d&
    report_to=now
```

### Save report to `Google Cloud Storage` and send Email
```
GET https://monitor-report-30508068041.asia-east1.run.app?
    dashboard_uid=abc123&
    report_from=now-30d&
    report_to=now&
    email_receivers=user1@example.com,user2@example.com&
    email_subject=Weekly Report&
    email_text_body=Please find attached the weekly report.
```

### Save with custom storage folder
```
GET https://monitor-report-30508068041.asia-east1.run.app?
    dashboard_uid=abc123&
    report_from=now-30d&
    report_to=now&
    storage_folder=2025-05
```

## Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `dashboard_uid` | string | Unique identifier of the Grafana dashboard | `abc123` |
| `report_from` | string | Start time for the report in Unix timestamp or relative time | `now-30d` |
| `report_to` | string | End time for the report in Unix timestamp or relative time | `now` |

## Optional Parameters

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `report_servergroup` | string | `All` | Server group filter for the report | `production` |
| `report_instance` | string | `All` | Instance filter for the report | `server-1` |
| `report_interval` | string | `30s` | Time interval for the report data | `1h` |
| `shutdown_instance` | boolean | `true` | Whether to shutdown the VM after report generation | `false` |
| `storage_folder` | string | Current month (YYYY-MM) | GCS folder path for storing the report | `2024-05` |
| `email_receivers` | string | `""` | Comma-separated list of email recipients | `user1@example.com,user2@example.com` |
| `email_text_body` | string | `"Monthly Monitor Report is ready."` | Email body text | `"Please find attached the weekly report."` |
| `email_subject` | string | `"Monthly Monitor Report"` | Email subject | `"Weekly System Report"` |
| `email_file_name` | string | Generated filename | Name of the file in the email attachment | `"weekly-report.pdf"` |

## Response

### Success Response
```json
{
    "message": "Successfully generated report for dashboard {dashboard_uid}"
}
```

### Error Response
```json
{
    "error": "Error message description"
}
```

## Notes

1. The function creates a temporary VM instance for report generation
2. Reports are stored in `Google Cloud Storage` bucket `cw-general` under the `monitor-report` path
4. The VM instance is automatically shut down after report generation unless `shutdown_instance=false`
5. All sensitive credentials (Grafana token, SMTP2Go API key) are stored in `Google Cloud Secret Manager`

## Dependencies

- Google Cloud Functions
- Google Cloud Storage
- Google Cloud Secret Manager
- Google Cloud Compute Engine
- SMTP2Go API
- Grafana Dashboard Reporter Plugin

# Deploy the function to Google Cloud Run
  ```bash
  gcloud run deploy monitor-report \
    --source . \
    --region asia-east1 \
    --project=codeworks-457009
  ```

