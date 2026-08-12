from email.message import EmailMessage
import base64
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def launch_client_login():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    print("token.json saved successfully")

def _load_token():
    credential = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    return credential


def send_email(download_id, downloads_log):
    email = downloads_log[download_id]["email"]
    path = Path(downloads_log[download_id]["file_path"])
    title = path.name

    FEEDBACK_FORM_URL = "https://docs.google.com/forms/d/1q1PuSkATLGkxlXoLwoHQz-p5zeex_Hbk4oFf56cUKK8/viewform"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; border: 1px solid #D2D4D6; border-radius: 12px; overflow: hidden;">

        <!-- Header -->
        <div style="background-color: #821019; padding: 24px 32px;">
        <p style="margin: 0; color: #ffffff; font-size: 18px; font-weight: bold; letter-spacing: 0.02em;">
            DLMC Video Downloader
        </p>
        </div>

        <!-- Body -->
        <div style="padding: 32px;">
        <p style="font-size: 16px; color: #000000; margin: 0 0 12px;">
            Hi there,
        </p>
        <p style="font-size: 15px; color: #000000; margin: 0 0 8px;">
            Your download is ready:
        </p>
        <p style="font-size: 15px; font-weight: bold; color: #821019; margin: 0 0 24px;">
            {title}
        </p>
        <p style="font-size: 14px; color: #5A646E; margin: 0 0 28px;">
            Return to the DLMC Video Downloader to save your file. Files are available for 24 hours before being automatically removed.
        </p>

        <!-- Feedback button -->
        <p style="font-size: 14px; color: #5A646E; margin: 0 0 16px;">
            The DLMC Video Downloader is in early release. Help us improve it by filling out our quick 1–2 minute
            <a href="{FEEDBACK_FORM_URL}" style="color: #821019; font-weight: bold;">feedback form</a>.
        </p>
        </div>

        <!-- Footer -->
        <div style="border-top: 1px solid #D2D4D6; padding: 20px 32px; background-color: #faf6f0;">
        <p style="margin: 0; font-size: 13px; color: #5A646E; line-height: 1.6;">
            --<br>
            Media Mentor on Duty<br>
            <a href="https://www.colgate.edu/about/campus-services-resources/digital-learning-media-center"
                style="color: #821019;">Digital Learning &amp; Media Center</a><br>
            Case-Geyer Library Level 5<br>
            (315) 228-6447
        </p>
        </div>

    </div>
    """

    msg = EmailMessage()
    msg["Subject"] = "Your Download is Ready — DLMC Video Downloader"
    msg["From"] = "gatedlmc@colgate.edu"
    msg["To"] = email
    msg.set_content("Your download is ready. Please return to the DLMC Video Downloader to save your file.")
    msg.add_alternative(html_body, subtype="html")

    creds = _load_token()
    service = build("gmail", "v1", credentials=creds)

    encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    send_request = {"raw": encoded_message}
    service.users().messages().send(userId="me", body=send_request).execute()

if __name__ == "__main__":
    launch_client_login()