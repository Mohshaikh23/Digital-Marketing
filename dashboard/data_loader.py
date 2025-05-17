import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime, timedelta
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cache directory setup
CACHE_DIR = Path('data_cache')
CACHE_DIR.mkdir(exist_ok=True)
CACHE_EXPIRY_HOURS = 6  # Data will be considered fresh for 6 hours

@st.cache_resource
def connect_to_google_sheets():
    """Establish and cache connection to Google Sheets"""
    try:
        if "gcp_service_account" not in st.secrets:
            logger.error("Google service account credentials not found in secrets")
            return None
            
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        return gspread.authorize(credentials)
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return None

def get_cache_filepath(sheet_name):
    """Get path for cached sheet data"""
    return CACHE_DIR / f"{sheet_name.lower().replace(' ', '_')}.csv"

def is_cache_valid(cache_file):
    """Check if cached data is still valid"""
    if not cache_file.exists():
        return False
    file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
    return file_age <= timedelta(hours=CACHE_EXPIRY_HOURS)

def save_to_cache(df, sheet_name):
    """Save DataFrame to cache"""
    cache_file = get_cache_filepath(sheet_name)
    try:
        df.to_csv(cache_file, index=False)
        logger.info(f"Saved {sheet_name} data to cache")
    except Exception as e:
        logger.error(f"Error saving {sheet_name} to cache: {str(e)}")

def load_from_cache(sheet_name):
    """Load DataFrame from cache"""
    cache_file = get_cache_filepath(sheet_name)
    if not cache_file.exists():
        return None
    try:
        return pd.read_csv(cache_file)
    except Exception as e:
        logger.error(f"Error loading {sheet_name} from cache: {str(e)}")
        return None

def safe_get_records(worksheet):
    """Ultra-robust worksheet data extraction with multiple fallbacks"""
    try:
        # Attempt 1: Standard get_all_records
        try:
            records = worksheet.get_all_records(expected_headers=1)
            if records and isinstance(records, list):
                return records
        except:
            pass

        # Attempt 2: Raw values with header detection
        values = worksheet.get_all_values()
        if not values:
            return []

        # Find header row (first non-empty row)
        header_row = 0
        for i, row in enumerate(values):
            if any(cell.strip() for cell in row):
                header_row = i
                break

        headers = values[header_row]
        records = []
        
        # Process data rows
        for row in values[header_row + 1:]:
            if len(row) != len(headers):
                continue
            record = {}
            for h, v in zip(headers, row):
                if h:  # Only add non-empty headers
                    record[h] = v
            if record:  # Only add non-empty records
                records.append(record)

        # Convert numeric columns
        for record in records:
            for key, value in record.items():
                if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                    record[key] = float(value)
                elif isinstance(value, str) and value.isdigit():
                    record[key] = int(value)
                    
        return records

    except Exception as e:
        logger.error(f"Failed to get records from {worksheet.title}: {str(e)}")
        return []

@st.cache_data(ttl=timedelta(hours=CACHE_EXPIRY_HOURS))
def load_sheet_data(_gc, spreadsheet_url, sheet_name=None):
    """Load data with comprehensive error handling"""
    try:
        spreadsheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = _gc.open_by_key(spreadsheet_id)
        
        if sheet_name:
            # Single worksheet load
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                records = safe_get_records(worksheet)
                df = pd.DataFrame(records) if records else pd.DataFrame()
                
                # Basic cleaning
                df = df.dropna(how='all').reset_index(drop=True)
                df.columns = df.columns.str.strip()
                
                # Convert date columns
                date_cols = [col for col in df.columns if any(x in col.lower() for x in ['date', 'time'])]
                for col in date_cols:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                
                return df
            except Exception as e:
                logger.error(f"Failed to load {sheet_name}: {str(e)}")
                return pd.DataFrame()
                
        else:
            # Load all worksheets
            all_data = {}
            for worksheet in spreadsheet.worksheets():
                try:
                    records = safe_get_records(worksheet)
                    if records:
                        df = pd.DataFrame(records)
                        df = df.dropna(how='all').reset_index(drop=True)
                        all_data[worksheet.title] = df
                except Exception as e:
                    logger.error(f"Skipped {worksheet.title}: {str(e)}")
                    continue
                    
            return all_data
            
    except Exception as e:
        logger.error(f"Spreadsheet access error: {str(e)}")
        return {} if sheet_name is None else pd.DataFrame()


def load_facebook_data():
    """Load Facebook data with improved error handling"""
    cache_file = get_cache_filepath("facebook")
    if cache_file.exists() and is_cache_valid(cache_file):
        return pd.read_csv(cache_file)
        
    try:
        gc = connect_to_google_sheets()
        if not gc:
            return load_from_cache("facebook") or pd.DataFrame()
            
        spreadsheet = gc.open_by_key("17gv72J54TDcW9wSAtG0cKGXty0zxfgeKZVLEp65bYcc")
        try:
            worksheet = spreadsheet.worksheet("Facebook_data")
            records = safe_get_records(worksheet)
            if not records:
                return load_from_cache("facebook") or pd.DataFrame()
                
            data = pd.DataFrame(records)
            
            # Data cleaning
            data.columns = [col.strip() for col in data.columns]
            date_cols = [col for col in data.columns if 'date' in col.lower()]
            for col in date_cols:
                data[col] = pd.to_datetime(data[col], errors='coerce')
            data = data.dropna(how='all')
            
            save_to_cache(data, "facebook")
            return data
            
        except gspread.WorksheetNotFound:
            logger.warning("Facebook_data worksheet not found")
            return load_from_cache("facebook") or pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error loading Facebook data: {str(e)}")
        return load_from_cache("facebook") or pd.DataFrame()


def load_instagram_data():
    """Load Instagram data with caching"""
    cache_file = get_cache_filepath("instagram")
    if cache_file.exists() and is_cache_valid(cache_file):
        return pd.read_csv(cache_file)
        
    try:
        gc = connect_to_google_sheets()
        if not gc:
            return load_from_cache("instagram") or pd.DataFrame()
            
        spreadsheet = gc.open("Data")
        worksheet = spreadsheet.worksheet("Instagram_data")
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Standardize column names
        data.columns = [col.strip() for col in data.columns]
        
        # Convert date columns
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            
        # Save to cache
        save_to_cache(data, "instagram")
        return data
        
    except Exception as e:
        logger.error(f"Error loading Instagram data: {str(e)}")
        return load_from_cache("instagram") or pd.DataFrame()

def load_linkedin_data():
    """Load LinkedIn data with caching - returns (metrics_df, posts_df)"""
    metrics_cache = get_cache_filepath("linkedin_metrics")
    posts_cache = get_cache_filepath("linkedin_posts")
    
    # Try to load from cache first
    if metrics_cache.exists() and posts_cache.exists() and is_cache_valid(metrics_cache) and is_cache_valid(posts_cache):
        return pd.read_csv(metrics_cache), pd.read_csv(posts_cache)
        
    try:
        gc = connect_to_google_sheets()
        if not gc:
            cached_metrics = load_from_cache("linkedin_metrics") or pd.DataFrame()
            cached_posts = load_from_cache("linkedin_posts") or pd.DataFrame()
            return cached_metrics, cached_posts
            
        spreadsheet = gc.open("Data")
        
        # Load metrics
        try:
            metrics_ws = spreadsheet.worksheet("SM_Link_Metrics")
            metrics_df = pd.DataFrame(metrics_ws.get_all_records())
            if 'Date' in metrics_df.columns:
                metrics_df['Date'] = pd.to_datetime(metrics_df['Date'], errors='coerce')
            save_to_cache(metrics_df, "linkedin_metrics")
        except Exception as e:
            logger.error(f"Error loading LinkedIn metrics: {str(e)}")
            metrics_df = load_from_cache("linkedin_metrics") or pd.DataFrame()
        
        # Load posts
        try:
            posts_ws = spreadsheet.worksheet("SM_Link_Posts")
            posts_df = pd.DataFrame(posts_ws.get_all_records())
            date_col = next((col for col in posts_df.columns if 'date' in col.lower()), None)
            if date_col:
                posts_df[date_col] = pd.to_datetime(posts_df[date_col], errors='coerce')
            save_to_cache(posts_df, "linkedin_posts")
        except Exception as e:
            logger.error(f"Error loading LinkedIn posts: {str(e)}")
            posts_df = load_from_cache("linkedin_posts") or pd.DataFrame()
            
        return metrics_df, posts_df
        
    except Exception as e:
        logger.error(f"Error loading LinkedIn data: {str(e)}")
        return (
            load_from_cache("linkedin_metrics") or pd.DataFrame(),
            load_from_cache("linkedin_posts") or pd.DataFrame()
        )

def load_youtube_data():
    cache_file = get_cache_filepath("youtube")
    if cache_file.exists() and is_cache_valid(cache_file):
        return pd.read_csv(cache_file)
        
    try:
        gc = connect_to_google_sheets()
        if not gc:
            return load_from_cache("youtube") or pd.DataFrame()
            
        spreadsheet = gc.open("Data")
        try:
            worksheet = spreadsheet.worksheet("YouTube_data")
        except gspread.WorksheetNotFound:
            logger.warning("YouTube_data worksheet not found")
            return load_from_cache("youtube") or pd.DataFrame()
            
        records = worksheet.get_all_records(expected_headers=1)
        data = pd.DataFrame(records)
        
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            
        save_to_cache(data, "youtube")
        return data
        
    except Exception as e:
        logger.error(f"Error loading YouTube data: {str(e)}")
        return load_from_cache("youtube") or pd.DataFrame()


def load_x_data():
    """Load X (Twitter) data with caching"""
    cache_file = get_cache_filepath("x_data")
    if cache_file.exists() and is_cache_valid(cache_file):
        return pd.read_csv(cache_file)
        
    try:
        gc = connect_to_google_sheets()
        if not gc:
            return load_from_cache("x_data") or pd.DataFrame()
            
        spreadsheet = gc.open("Data")
        worksheet = spreadsheet.worksheet("X_data")
        data = pd.DataFrame(worksheet.get_all_records())
        
        # Convert date column
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
            
        # Save to cache
        save_to_cache(data, "x_data")
        return data
        
    except Exception as e:
        logger.error(f"Error loading X data: {str(e)}")
        return load_from_cache("x_data") or pd.DataFrame()

def clear_all_cache():
    """Clear all cached data files"""
    for f in CACHE_DIR.glob("*.csv"):
        try:
            f.unlink()
            logger.info(f"Deleted cache file: {f.name}")
        except Exception as e:
            logger.error(f"Error deleting cache file {f.name}: {str(e)}")
    logger.info("All cache files cleared")