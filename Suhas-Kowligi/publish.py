import json
import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configuration
SCOPES = ["https://www.googleapis.com/auth/drive"]
EXISTING_FILE_ID = "1wDLuXtxKjuxr-RzIDFP4-GdRqCx7JfFs"  # Replace with your file ID
FILE_TO_UPLOAD = "resume.pdf"  # Your file to upload
# Absolute path for CLIENT_SECRET_FILE
CLIENT_SECRET_FILE = "/Users/gandalf/Documents/portfolio/Suhas-Kowligi/client_secret_2_188248758691-imga0p9eghv8dlbnndo1k2kj19us3vi5.apps.googleusercontent.com.json"


def get_authenticated_service():
    """Handle authentication with robust error handling for expired tokens."""
    creds = None

    # Check for existing token
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            print("✅ Loaded credentials from token.json")
        except Exception:
            print("⚠️ token.json was corrupt or empty. Starting fresh authentication.")
            creds = None

    # Verify validity and attempt refresh if necessary
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                print("🔄 Attempting to refresh expired token...")
                creds.refresh(Request())
                print("✅ Token refreshed successfully.")
            except RefreshError:
                print("❌ Refresh token is invalid or expired. Re-authenticating...")
                creds = None  # Reset creds to trigger the login flow below
            except Exception as e:
                print(f"❌ Unexpected error during refresh: {e}")
                creds = None

    # If no valid credentials (either didn't exist, or refresh failed)
    if not creds or not creds.valid:
        print(f"""
        =============================================
        Authentication Required!
        Attempting to load client secret from '{CLIENT_SECRET_FILE}'.
        Please ensure this file is present and is a valid OAuth 2.0 client secret file
        downloaded for a 'Desktop app' from Google Cloud Console.
        =============================================
        """)

        # Load client configuration from file
        if not os.path.exists(CLIENT_SECRET_FILE):
            print(f"❌ Error: Client secret file not found at '{CLIENT_SECRET_FILE}'.")
            print("Please provide the correct path to your client secret JSON file.")
            return None

        try:
            with open(CLIENT_SECRET_FILE, "r") as f:
                client_config = json.load(f)
        except json.JSONDecodeError as e:
            print(
                f"❌ Error: Could not decode JSON from '{CLIENT_SECRET_FILE}'. Check file integrity. Details: {e}"
            )
            return None
        except Exception as e:
            print(
                f"❌ An unexpected error occurred while reading client secret file: {e}"
            )
            return None

        # InstalledAppFlow.from_client_config expects the full dictionary (which includes the "installed" key)
        # when loading from a file that contains the "installed" key at the root.
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save new credentials
        with open("token.json", "w") as token:
            token.write(creds.to_json())
            print("✅ New token saved to token.json")

    # If creds is still None after attempting all authentication methods, return None.
    if creds is None:
        return None

    return build("drive", "v3", credentials=creds)


def upload_new_version():
    """Upload new version of existing file"""
    if not os.path.exists(FILE_TO_UPLOAD):
        print(f"Error: File '{FILE_TO_UPLOAD}' not found!")
        return

    # This will now handle the re-auth flow automatically if needed
    service = get_authenticated_service()

    # Handle the case where authentication failed
    if service is None:
        print("Authentication failed. Aborting file upload.")
        return

    try:
        # Get file metadata
        file = (
            service.files()
            .get(fileId=EXISTING_FILE_ID, fields="name,mimeType")
            .execute()
        )

        print(f"Found file: {file.get('name')} (MIME: {file.get('mimeType')})")

        # Upload new version
        media = MediaFileUpload(
            FILE_TO_UPLOAD, mimetype=file["mimeType"], resumable=True
        )

        print("Uploading new version...")
        updated_file = (
            service.files()
            .update(fileId=EXISTING_FILE_ID, media_body=media, fields="id,name,version")
            .execute()
        )

        print(
            f"\n✅ Successfully updated '{updated_file['name']}' (ID: {updated_file['id']})"
        )
        print("Note: All previous versions are preserved in Google Drive")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Possible solutions:")
        print("- Verify the file ID exists and you have edit permissions")
        print("- Check your internet connection")
        print(
            "- Ensure your client_secret.json file is correctly configured for Google Drive API access."
        )
        # No need to suggest deleting token.json anymore; the script handles it!


if __name__ == "__main__":
    print("Google Drive File Version Updater")
    upload_new_version()
