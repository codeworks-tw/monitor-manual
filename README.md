# Monitor Manual

## Directory Overview

- **`master/`**  
  Contains the main monitoring infrastructure setup including Docker configurations for Prometheus, Grafana, and additional services like report generation and headless Chrome. Includes various docker-compose configurations for different deployment scenarios.

- **`target/`**  
  Contains deployment configurations for monitoring targets, including Docker setup and Nginx configuration for secure access to monitoring endpoints.

- **`report-cloud-run-function/`**  
  Contains the source code for a Cloud Run function that generates monitoring reports

  # Deploy the monitoring report function to Google Cloud Run
  ```bash
  gcloud run deploy monitor-report \
    --source . \
    --region asia-east1 \
    --project=codeworks-457009
  ```
