import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import pandas as pd
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_google_credentials() -> Credentials:
    """Gets valid user credentials from storage or initiates OAuth2 flow."""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            # Start local server for authentication
            # Clean up any existing token
            if os.path.exists('token.pickle'):
                os.remove('token.pickle')
                logger.info("Removed existing token.pickle")
            
            # Start local server for authentication
            import socket
            def find_free_port():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    s.listen(1)
                    port = s.getsockname()[1]
                return port
            
            port = find_free_port()
            print(f"\n=== Google Sheets Authentication ===")
            print(f"1. Local server starting on port {port}")
            print("2. Please wait for the authentication URL...")
            print("3. When prompted, copy and paste the URL in your browser")
            print("4. Complete the authentication in your browser\n")
            
            try:
                creds = flow.run_local_server(
                    port=port,
                    open_browser=False,
                    timeout_seconds=300,  # 5 minute timeout
                    success_message="Authentication completed! You can close this window."
                )
                print("\n=== Authentication completed successfully! ===")
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                print("\nPlease try again and make sure to:")
                print("1. Use the latest URL provided")
                print("2. Complete the authentication process in your browser")
                print("3. Don't close the browser until redirected to success page")
                raise
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def get_sheets_service():
    """Creates and returns Google Sheets API service."""
    creds = get_google_credentials()
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def process_sheet_values(values: List[List[str]], sheet_name: str) -> pd.DataFrame:
    """
    Process sheet values into a DataFrame, handling varying column counts.
    
    Args:
        values (List[List[str]]): Raw values from the sheet
        sheet_name (str): Name of the sheet for logging
        
    Returns:
        pd.DataFrame: Processed DataFrame
    """
    if not values:
        return pd.DataFrame()
        
    # Get the first row as header
    header = values[0]
    data_rows = values[1:]
    
    # Find the maximum number of columns in data rows
    data_cols = max(len(row) for row in data_rows) if data_rows else len(header)
    header_cols = len(header)
    max_cols = max(data_cols, header_cols)
    
    if max_cols > header_cols:
        # Add generic column names for extra columns
        header.extend([f'{sheet_name}_Column{i+1}' for i in range(header_cols, max_cols)])
        logger.info(f"Added {max_cols - header_cols} column headers to sheet '{sheet_name}'")
        
    # Pad all data rows to max_cols
    padded_data = [
        row + [''] * (max_cols - len(row))
        for row in data_rows
    ]
    
    return pd.DataFrame(padded_data, columns=header)

def get_sheet_data(spreadsheet_id: str) -> Dict[str, pd.DataFrame]:
    """
    Gets all sheets from a Google Spreadsheet and returns them as DataFrames.
    
    Args:
        spreadsheet_id (str): The ID of the spreadsheet
        
    Returns:
        Dict[str, pd.DataFrame]: Dictionary with sheet names as keys and DataFrames as values
    """
    try:
        sheets = get_sheets_service()
        
        # Get all sheet names
        sheet_metadata = sheets.get(spreadsheetId=spreadsheet_id).execute()
        sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
        
        # Create a dictionary to store DataFrames
        dataframes = {}
        
        # Get data from each sheet
        for sheet_name in sheet_names:
            logger.info(f"Processing sheet: {sheet_name}")
            
            try:
                # Get the sheet data
                result = sheets.values().get(
                    spreadsheetId=spreadsheet_id,
                    range=sheet_name
                ).execute()
                
                values = result.get('values', [])
                
                if not values:
                    logger.warning(f"No data found in sheet: {sheet_name}")
                    continue
                
                # Process the sheet values into a DataFrame
                df = process_sheet_values(values, sheet_name)
                if not df.empty:
                    dataframes[sheet_name] = df
                    logger.info(f"Successfully processed sheet '{sheet_name}' with {len(df.columns)} columns")
                
            except Exception as e:
                logger.error(f"Error processing sheet {sheet_name}: {str(e)}")
                continue
            
        return dataframes
        
    except Exception as e:
        logger.error(f"Error processing spreadsheet: {str(e)}")
        raise

def export_to_csv(dataframes: Dict[str, pd.DataFrame], output_dir: str = 'output'):
    """
    Exports each DataFrame to a CSV file.
    
    Args:
        dataframes (Dict[str, pd.DataFrame]): Dictionary of sheet names and their DataFrames
        output_dir (str): Directory to save CSV files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for sheet_name, df in dataframes.items():
        output_path = os.path.join(output_dir, f"{sheet_name}.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {sheet_name} to {output_path}")

def main():
    """Main function to process Google Sheets and export to CSV."""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get the spreadsheet ID from environment variable
        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        if not spreadsheet_id:
            raise ValueError("SPREADSHEET_ID environment variable is not set")
        
        # Get data from all sheets
        logger.info("Getting data from Google Sheets...")
        dataframes = get_sheet_data(spreadsheet_id)
        
        # Export to CSV
        logger.info("Exporting to CSV files...")
        export_to_csv(dataframes)
        
        logger.info("Process completed successfully!")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()