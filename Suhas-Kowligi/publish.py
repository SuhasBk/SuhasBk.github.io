import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
EXISTING_FILE_ID = '1wDLuXtxKjuxr-RzIDFP4-GdRqCx7JfFs'  # Replace with your file ID
FILE_TO_UPLOAD = 'resume.pdf'  # Your file to upload

def get_authenticated_service():
    """Handle authentication with or without credentials.json"""
    creds = None
    
    # Check for existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, create them interactively
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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
                    "client_id": input("Enter client_id: "),
                    "client_secret": input("Enter client_secret: "),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def upload_new_version():
    """Upload new version of existing file"""
    if not os.path.exists(FILE_TO_UPLOAD):
        print(f"Error: File '{FILE_TO_UPLOAD}' not found!")
        return
    
    service = get_authenticated_service()
    
    try:
        # Get file metadata
        file = service.files().get(
            fileId=EXISTING_FILE_ID,
            fields='name,mimeType'
        ).execute()
        
        # Upload new version
        media = MediaFileUpload(
            FILE_TO_UPLOAD,
            mimetype=file['mimeType'],
            resumable=True
        )
        
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
        print("- Try deleting token.json and re-authenticating")

if __name__ == '__main__':
    print("Google Drive File Version Updater")
    upload_new_version()