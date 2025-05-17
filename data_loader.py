import streamlit as st
import os
import pandas as pd
import gspread
from google.oauth2 import service_account
from typing import Optional, Union, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Google Sheets connection with proper caching
@st.cache_resource
def connect_to_google_sheets() -> gspread.client.Client:
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

# Improved data loading with better type hints and error handling
@st.cache_data(ttl=3600)
def load_sheet_data(spreadsheet_url, worksheet_name=None):
    try:
        gc = connect_to_google_sheets()
        if gc is None:
            st.error("Failed to connect to Google Sheets")
            return pd.DataFrame()
        
        # Extract spreadsheet ID from URL
        if '/d/' in spreadsheet_url:
            spreadsheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        else:
            spreadsheet_id = spreadsheet_url
            
        spreadsheet = gc.open_by_key(spreadsheet_id)
        
        # Special handling for demographics data
        if worksheet_name == "demographics":
            worksheet = spreadsheet.worksheet("demographics")
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Convert date column if exists
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
            # Ensure numeric columns
            numeric_cols = ['users', 'engagedSessions', 'engagementRate']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            return df
            
        # Default handling for other worksheets
        if worksheet_name:
            worksheet = spreadsheet.worksheet(worksheet_name)
            return pd.DataFrame(worksheet.get_all_records())
        
        # Load all worksheets
        return {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
                
    except Exception as e:
        return pd.DataFrame()


# Enhanced data validation (silent version)
def validate_data(
    df: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
    required_columns: list
) -> bool:
    """Validate dataframe(s) have required columns"""
    if df is None:
        return False
        
    if isinstance(df, dict):
        return all(validate_data(d, required_columns) for d in df.values())
    
    return all(col in df.columns for col in required_columns)

# Improved date filtering (silent version)
def filter_data_by_date(
    data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
    start_date: Union[str, pd.Timestamp], 
    end_date: Union[str, pd.Timestamp]
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Filter already-loaded data by date range (for display only)"""
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        return data
        
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    if isinstance(data, dict):
        return {k: filter_data_by_date(v, start_date, end_date) for k, v in data.items()}
    
    # Handle different possible date column names
    date_col = next(
        (col for col in data.columns 
         if any(x in col.lower() for x in ['date', 'time', 'created', 'published'])),
        None
    )
    
    if not date_col:
        return data
        
    return data[
        (pd.to_datetime(data[date_col]) >= start_date) & 
        (pd.to_datetime(data[date_col]) <= end_date)
    ]


# Social media data loading with better type hints (silent version)
def load_social_media_data_from_sheet(
    sheet_name: str, 
    worksheet_name: str
) -> Optional[pd.DataFrame]:
    """Load social media data from specific sheet"""
    try:
        gc = connect_to_google_sheets()
        if gc is None:
            return pd.DataFrame()
            
        sheet = gc.open(sheet_name)
        worksheet = sheet.worksheet(worksheet_name)
        return pd.DataFrame(worksheet.get_all_records())
    except Exception as e:
        logger.error(f"Error loading {sheet_name}/{worksheet_name}: {e}")
        return pd.DataFrame()

# LinkedIn data loading with tuple return (silent version)
def load_linkedin_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load LinkedIn posts and metrics from specific worksheets"""
    try:
        gc = connect_to_google_sheets()
        if gc is None:
            st.error("Failed to connect to Google Sheets")
            return pd.DataFrame(), pd.DataFrame()
        
        # Open the spreadsheet by its exact name (case-sensitive)
        try:
            spreadsheet = gc.open("Data")  # Update this to your exact spreadsheet name
        except gspread.SpreadsheetNotFound:
            st.error("Spreadsheet 'LinkedIn_Data' not found. Please check the name.")
            return pd.DataFrame(), pd.DataFrame()
        
        # Load posts data
        try:
            posts_worksheet = spreadsheet.worksheet("SM_Link_Posts")
            posts_data = posts_worksheet.get_all_records()
            posts_df = pd.DataFrame(posts_data)
            
            # Convert date columns
            date_cols = [col for col in posts_df.columns if 'date' in col.lower()]
            for col in date_cols:
                posts_df[col] = pd.to_datetime(posts_df[col], errors='coerce')
        except gspread.WorksheetNotFound:
            st.error("Worksheet 'SM_Link_Posts' not found")
            posts_df = pd.DataFrame()
        
        # Load metrics data
        try:
            metrics_worksheet = spreadsheet.worksheet("SM_Link_Metrics")
            metrics_data = metrics_worksheet.get_all_records()
            metrics_df = pd.DataFrame(metrics_data)
            
            # Convert date column
            if 'Date' in metrics_df.columns:
                metrics_df['Date'] = pd.to_datetime(metrics_df['Date'], errors='coerce')
        except gspread.WorksheetNotFound:
            st.error("Worksheet 'SM_Link_Metrics' not found")
            metrics_df = pd.DataFrame()
            
        return posts_df, metrics_df
        
    except Exception as e:
        st.error(f"Error loading LinkedIn data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()


# Improved Facebook data loading (silent version)
def load_facebook_data(filename="facebook_data.csv"):
    try:
        if not os.path.exists(filename):
            return pd.DataFrame(columns=["Publish time", "Title", "Reach", "Reactions, comments and shares"])
        return pd.read_csv(filename)
    except Exception as e:
        logger.error(f"Error loading Facebook data: {e}")
        return pd.DataFrame(columns=["Publish time", "Title", "Reach", "Reactions, comments and shares"])

# Instagram data loader (silent version)
def load_instagram_data(filename="instagram_data.csv"):
    try:
        if not os.path.exists(filename):
            return pd.DataFrame(columns=["Date", "Title", "Reach", "Likes", "Comments"])
        return pd.read_csv(filename)
    except Exception as e:
        logger.error(f"Error loading Instagram data: {e}")
        return pd.DataFrame(columns=["Date", "Title", "Reach", "Likes", "Comments"])


@st.cache_data
def load_ecommerce_data(_gc, spreadsheet_url):
    """Load e-commerce data"""
    try:
        data = load_sheet_data(_gc, spreadsheet_url, "ecommerce")
        if data.empty:
            return pd.DataFrame(columns=["date", "productName", "itemRevenue"])
            
        # Ensure date column is properly formatted
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            
        return data
    except Exception as e:
        st.error(f"Error loading e-commerce data: {e}")
        return pd.DataFrame(columns=["date", "productName", "itemRevenue"])

@st.cache_data
def load_retention_data(_gc, spreadsheet_url):
    """Load retention data"""
    try:
        data = load_sheet_data(_gc, spreadsheet_url, "retention")
        if data.empty:
            return pd.DataFrame(columns=["date", "cohort", "retentionRate"])
            
        return data
    except Exception as e:
        st.error(f"Error loading retention data: {e}")
        return pd.DataFrame(columns=["date", "cohort", "retentionRate"])

@st.cache_data
def load_error_data(_gc, spreadsheet_url):
    """Load error tracking data"""
    try:
        data = load_sheet_data(_gc, spreadsheet_url, "errors")
        if data.empty:
            return pd.DataFrame(columns=["date", "eventName", "eventCount"])
            
        return data
    except Exception as e:
        st.error(f"Error loading error data: {e}")
        return pd.DataFrame(columns=["date", "eventName", "eventCount"])

# Generic data loader with improved caching
@st.cache_data
def load_data(filename: str) -> Optional[pd.DataFrame]:
    """Load and cache data from file"""
    try:
        data = pd.read_csv(filename)
        
        if data.empty:
            st.warning(f"File {filename} is empty")
            return None
            
        # Standard date column handling
        date_cols = [col for col in data.columns if 'date' in col.lower()]
        for col in date_cols:
            data[col] = pd.to_datetime(data[col], errors='coerce')
            
        return data
    except FileNotFoundError:
        st.error(f"File not found: {filename}")
        return None
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return None

# Growth calculation with validation
def calculate_growth(
    data: pd.DataFrame, 
    metric: str
) -> Optional[pd.DataFrame]:
    """Calculate weekly and monthly growth rates"""
    if data is None or data.empty or metric not in data.columns:
        return None
        
    data = data.copy()
    data['wow_growth'] = data[metric].pct_change(periods=7) * 100
    data['mom_growth'] = data[metric].pct_change(periods=30) * 100
    return data

# Delta calculation with edge case handling
def calculate_delta(
    current_value: float, 
    previous_value: float
) -> float:
    """Calculate percentage change between values"""
    if previous_value == 0:
        return 0.0
    return ((current_value - previous_value) / previous_value) * 100

# Post metrics with improved date handling
def calculate_post_metrics(
    posts_df: pd.DataFrame
) -> Optional[pd.DataFrame]:
    """Calculate weekly post metrics"""
    if posts_df is None or posts_df.empty:
        return None

    # Find date column
    date_col = next(
        (col for col in posts_df.columns 
         if any(x in col.lower() for x in ['date', 'created', 'published'])),
        None
    )
    
    if not date_col:
        st.error("No valid date column found")
        return None
        
    try:
        posts_df = posts_df.copy()
        posts_df['date'] = pd.to_datetime(posts_df[date_col])
        posts_df['week'] = posts_df['date'].dt.to_period('W').astype(str)
        
        weekly_stats = posts_df.groupby('week').agg(
            num_posts=('date', 'count'),
            avg_engagement=('likes', 'mean')
        ).reset_index()
        
        weekly_stats['post_growth'] = weekly_stats['num_posts'].pct_change() * 100
        return weekly_stats
    except Exception as e:
        st.error(f"Error calculating post metrics: {e}")
        return None