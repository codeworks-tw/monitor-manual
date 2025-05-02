from google.cloud import storage, secretmanager
from config import PROJECT
import base64
import requests

def get_secret_value(secret_id, version_id = "latest"):
    """
    Retrieves a secret value from Google Cloud Platform Secret Manager.

    Args:
        secret_id (str): The name/ID of the secret to retrieve
        version_id (str, optional): The version of the secret. Defaults to "latest"

    Returns:
        str: The decoded secret value, or empty string if not found
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    token = response.payload.data.decode("UTF-8")
    return token or ""

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """
    Uploads a local file to Google Cloud Storage bucket.

    Args:
        bucket_name (str): The name of the GCS bucket (e.g., 'cw-general')
        source_file_name (str): Path to the local file to upload
        destination_blob_name (str): Destination path in the GCS bucket (e.g., 'monitor-report/report.pdf')

    Prints:
        Success message with upload details
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    print(f"✅ File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")

def send_email(file_path, file_name, email_receivers, email_subject = "Monthly Monitor Report", email_text_body = "Monthly Monitor Report is ready."):
    """
    Sends an email with an attached file using SMTP2Go API.

    Args:
        file_path (str): Path to the local file to be attached
        file_name (str): Name to be used for the attached file in the email
        email_receivers (list[str]): List of email addresses (e.g. ["user1@gmail.com", "user2@gmail.com"])
        email_subject (str, optional): Email subject. Defaults to "Monthly Monitor Report"
        email_text_body (str, optional): Email body text. Defaults to "Monthly Monitor Report is ready."

    Prints:
        API response status code and JSON response
    """
    with open(file_path, "rb") as f:
        encoded_file = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "sender": "report@codeworkstw.com",
        "to": email_receivers,
        "subject": email_subject,
        "text_body": email_text_body,
        "attachments": [
            {
                "filename": file_name,
                "fileblob": encoded_file
            }
        ]
    }
    
    response = requests.post(
        "https://api.smtp2go.com/v3/email/send",
        headers={
            "X-Smtp2go-Api-Key": get_secret_value("smtp2go-api-key"),
            "Content-Type": "application/json"
        },
        json=payload
    )

    print(response.status_code, response.json())
