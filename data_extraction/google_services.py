# google_services.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
import logging
import os
from config import SERVICE_ACCOUNT_FILE, SCOPES

def initialize_services():
    try:
        # Convert to absolute path and normalize
        service_account_path = os.path.abspath(SERVICE_ACCOUNT_FILE)
        
        # Debugging - print where we're looking
        print(f"Looking for service account at: {service_account_path}")
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found at: {service_account_path}")
        
        # Initialize credentials
        creds = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=SCOPES
        )
        
        # Initialize services
        sheets_service = build('sheets', 'v4', credentials=creds)
        analytics_client = BetaAnalyticsDataClient(credentials=creds)
        
        return sheets_service, analytics_client
        
    except Exception as e:
        logging.error(f"Failed to initialize services: {e}")
        return None, None