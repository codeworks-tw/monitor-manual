#!/bin/bash

# Variables
INSTANCE_NAME="monitor-report-renderer-temp"
MACHINE_IMAGE="monitor-report-renderer"
ZONE="asia-east1-c"
NETWORK="cw-default"
SUBNET="sub-default"
PRIVATE_IP=""
PROJECT="codeworks-457009"
GRAFANA_TOKEN=""
OUTPUT_FILE="report1.pdf"
DASHBOARD_UID="20241225"

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
