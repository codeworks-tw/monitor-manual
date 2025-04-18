#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 --token=<token> --private-ip=<private-ip>"
    exit 1
}

# Default Variables
INSTANCE_NAME="monitor-report-renderer-temp"
MACHINE_IMAGE="monitor-report-renderer"
ZONE="asia-east1-c"
NETWORK="cw-default"
SUBNET="sub-default"
PROJECT="codeworks-457009"
OUTPUT_FILE="report1.pdf"
DASHBOARD_UID="20241225"

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --token=*) GRAFANA_TOKEN="${1#*=}" ;;
        --private-ip=*) PRIVATE_IP="${1#*=}" ;;
        *) usage ;;  # Display usage if an invalid argument is passed
    esac
    shift
done

# Validate that both token and private IP are provided
if [[ -z "$GRAFANA_TOKEN" || -z "$PRIVATE_IP" ]]; then
    echo "Both --token and --private-ip are required. Exiting..."
    exit 1  # Exit early if either value is not provided
fi

# Creating temporary compute instance from machine image
echo "🔧 Creating instance '$INSTANCE_NAME' from machine image..."
gcloud compute instances create "$INSTANCE_NAME" \
  --source-machine-image="$MACHINE_IMAGE" \
  --zone="$ZONE" \
  --network="$NETWORK" \
  --subnet="$SUBNET" \
  --private-network-ip="$PRIVATE_IP" \
  --project="$PROJECT"

# Retrieving external IP of monitor-master
echo "🌐 Getting external IP address of monitor-master..."
MONITOR_MASTER_IP=$(gcloud compute instances describe monitor-master \
  --zone="$ZONE" \
  --format="get(networkInterfaces[0].accessConfigs[0].natIP)" \
  --project="$PROJECT")

echo "✅ Monitor-master IP: $MONITOR_MASTER_IP"

# Waiting for instance and services to be fully up
echo "⏳ Waiting 5 seconds for services to be ready..."
sleep 5

# Downloading the Grafana report as PDF
echo "📥 Downloading report from Grafana..."
curl -o "$OUTPUT_FILE" \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  "http://$MONITOR_MASTER_IP:3000/api/plugins/mahendrapaipuri-dashboardreporter-app/resources/report?dashUid=$DASHBOARD_UID&from=now-5m&to=now&var-servergroup=All&var-instance=10.140.0.2:8080&var-interval=30s"

# Deleting temporary instance to save cost
echo "🗑️ Deleting temporary instance '$INSTANCE_NAME'..."
gcloud compute instances delete "$INSTANCE_NAME" \
  --zone="$ZONE" \
  --project="$PROJECT" \
  --quiet

# Done
echo "🎉 Done! Report saved as $OUTPUT_FILE"
