import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
EXISTING_FILE_ID = '1wDLuXtxKjuxr-RzIDFP4-GdRqCx7JfFs'  # Replace with your file ID
FILE_TO_UPLOAD = 'resume.pdf'  # Your file to upload

def get_authenticated_service():
    """Handle authentication with robust error handling for expired tokens."""
    creds = None
    
    # Check for existing token
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception:
            print("⚠️ token.json was corrupt or empty. Starting fresh authentication.")
            creds = None

    # Verify validity and attempt refresh if necessary
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                print("🔄 Attempting to refresh expired token...")
                creds.refresh(Request())
            except RefreshError:
                print("❌ Refresh token is invalid or expired. Re-authenticating...")
                creds = None  # Reset creds to trigger the login flow below
            except Exception as e:
                print(f"❌ Unexpected error during refresh: {e}")
                creds = None

    # If no valid credentials (either didn't exist, or refresh failed)
    if not creds or not creds.valid:
        print("""
        =============================================
        Follow these steps to authenticate:
        1. Go to https://console.cloud.google.com/
        2. Create a new project
        3. Enable 'Google Drive API'
        4. Create OAuth credentials (Desktop App type)
        5. Copy the below client configuration:
        =============================================
        """)
        
        client_config = {
            "installed": {
                "client_id": input("Enter client_id: ").strip(),
                "client_secret": input("Enter client_secret: ").strip(),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save new credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("✅ New token saved to token.json")
    
    return build('drive', 'v3', credentials=creds)

def upload_new_version():
    """Upload new version of existing file"""
    if not os.path.exists(FILE_TO_UPLOAD):
        print(f"Error: File '{FILE_TO_UPLOAD}' not found!")
        return
    
    # This will now handle the re-auth flow automatically if needed
    service = get_authenticated_service()
    
    try:
        # Get file metadata
        file = service.files().get(
            fileId=EXISTING_FILE_ID,
            fields='name,mimeType'
        ).execute()
        
        print(f"Found file: {file.get('name')} (MIME: {file.get('mimeType')})")
        
        # Upload new version
        media = MediaFileUpload(
            FILE_TO_UPLOAD,
            mimetype=file['mimeType'],
            resumable=True
        )
        
        print("Uploading new version...")
        updated_file = service.files().update(
            fileId=EXISTING_FILE_ID,
            media_body=media,
            fields='id,name,version'
        ).execute()
        
        print(f"\n✅ Successfully updated '{updated_file['name']}' (ID: {updated_file['id']})")
        print("Note: All previous versions are preserved in Google Drive")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Possible solutions:")
        print("- Verify the file ID exists and you have edit permissions")
        print("- Check your internet connection")
        # No need to suggest deleting token.json anymore; the script handles it!

if __name__ == '__main__':
    print("Google Drive File Version Updater")
    upload_new_version()