from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build
from config import SERVICE_ACCOUNT_FILE, SCOPES, SEARCH_CONSOLE_SITE_URL
from google.oauth2 import service_account
from config import SERVICE_ACCOUNT_FILE, SCOPES

def fetch_search_console_data(site_url):
    """Fetch Search Console data from Feb 10, 2025 to today"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        service = build('searchconsole', 'v1', credentials=creds)
        
        # Fixed start date of Feb 10, 2025
        start_date = "2025-02-10"
        end_date = datetime.now().strftime('%Y-%m-%d')

        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['date', 'query', 'page', 'country', 'device'],
            'rowLimit': 25000,
            'dataState': 'all'
        }

        response = service.searchanalytics().query(
            siteUrl=site_url, body=request).execute()
        
        if 'rows' not in response:
            print("⚠️ No Search Console data found")
            return pd.DataFrame()
            
        rows = []
        for row in response['rows']:
            rows.append({
                'date': row['keys'][0],
                'query': row['keys'][1],
                'page': row['keys'][2],
                'country': row['keys'][3],
                'device': row['keys'][4],
                'clicks': row['clicks'],
                'impressions': row['impressions'],
                'ctr': row['ctr'],
                'position': row['position']
            })
            
        df = pd.DataFrame(rows)
        
        # Calculate additional SEO metrics
        if not df.empty:
            df['traffic_share'] = df['clicks'] / df['clicks'].sum()
            df['impression_share'] = df['impressions'] / df['impressions'].sum()
        
        return df
        
    except Exception as e:
        print(f"❌ Search Console error: {e}")
        return pd.DataFrame()