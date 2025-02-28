from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import logging
import socket
from typing import Optional

logger = logging.getLogger(__name__)

class GoogleSheetsClient:
    """Handles Google Sheets API authentication and client operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        self.credentials_path = credentials_path
        self._sheets_service = None
    
    def _get_credentials(self) -> Credentials:
        """Gets valid user credentials from storage or initiates OAuth2 flow."""
        creds = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            creds = self._refresh_or_get_new_credentials(creds)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def _refresh_or_get_new_credentials(self, creds: Optional[Credentials]) -> Credentials:
        """Refreshes existing credentials or gets new ones through OAuth flow."""
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            return creds
            
        return self._initiate_oauth_flow()
    
    def _initiate_oauth_flow(self) -> Credentials:
        """Initiates OAuth2 flow for new credentials."""
        # Clean up any existing token
        if os.path.exists('token.pickle'):
            os.remove('token.pickle')
            logger.info("Removed existing token.pickle")
        
        flow = InstalledAppFlow.from_client_secrets_file(
            self.credentials_path, self.SCOPES)
        
        port = self._find_free_port()
        self._print_auth_instructions(port)
        
        try:
            creds = flow.run_local_server(
                port=port,
                open_browser=False,
                timeout_seconds=300,
                success_message="Authentication completed! You can close this window."
            )
            print("\n=== Authentication completed successfully! ===")
            return creds
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            print("\nPlease try again and make sure to:")
            print("1. Use the latest URL provided")
            print("2. Complete the authentication process in your browser")
            print("3. Don't close the browser until redirected to success page")
            raise
    
    @staticmethod
    def _find_free_port() -> int:
        """Finds an available port for the local server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    @staticmethod
    def _print_auth_instructions(port: int) -> None:
        """Prints authentication instructions for the user."""
        print(f"\n=== Google Sheets Authentication ===")
        print(f"1. Local server starting on port {port}")
        print("2. Please wait for the authentication URL...")
        print("3. When prompted, copy and paste the URL in your browser")
        print("4. Complete the authentication in your browser\n")
    
    def get_service(self):
        """Creates and returns Google Sheets API service."""
        if not self._sheets_service:
            creds = self._get_credentials()
            service = build('sheets', 'v4', credentials=creds)
            self._sheets_service = service.spreadsheets()
        return self._sheets_service