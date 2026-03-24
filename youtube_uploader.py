import os
from googleapiclient.discovery import build # type: ignore
from googleapiclient.http import MediaFileUpload # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from google.auth.transport.requests import Request # type: ignore
from google.oauth2.credentials import Credentials # type: ignore

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """Handles OAuth 2.0 authentication for YouTube API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('youtube', 'v3', credentials=creds)

def upload_video(video_path, title, description, tags=None):
    """Uploads the video directly to YouTube."""
    try:
        if tags is None:
            tags = ["automation", "shorts", "business", "ai"]
            
        print("\n[STEP 5] Authenticating with YouTube...")
        youtube = authenticate_youtube()
        
        # Determine if it's a short by tags/description
        if "#shorts" not in description.lower():
            description += "\n\n#shorts"
            
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22" # People & Blogs by default
            },
            "status": {
                "privacyStatus": "private", # Safest to upload as private first
                "selfDeclaredMadeForKids": False
            }
        }
        
        print(f"Uploading '{title}' to YouTube (Private)...")
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(video_path, mimetype='video/mp4', chunksize=1024*1024, resumable=True)
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
                
        print(f"✨ Successfully uploaded to YouTube: https://youtu.be/{response['id']}")
        return response['id']
        
    except Exception as e:
        print(f"❌ YouTube Upload failed: {str(e)}")
        return None

if __name__ == "__main__":
    print("Testing YouTube Uploader...")
