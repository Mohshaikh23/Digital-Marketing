# dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from data_extractor import refresh_data

# Configuration
SPREADSHEET_ID = "17gv72J54TDcW9wSAtG0cKGXty0zxfgeKZVLEp65bYcc"
SERVICE_ACCOUNT_FILE = "proefficient-data-entry-194479023ae8.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Initialize Google Sheets service
def init_gsheets():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Failed to initialize Google Sheets: {e}")
        return None

# Get data from Google Sheets with error handling
@st.cache_data(ttl=3600)
def get_sheet_data(sheet_name,refresh=False):
    """Add refresh parameter to force update"""
    if refresh:
        st.cache_data.clear()
    try:
        service = init_gsheets()
        if not service:
            return pd.DataFrame()
            
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z"
        ).execute()
        
        values = result.get('values', [])
        if not values:
            return pd.DataFrame()
            
        df = pd.DataFrame(values[1:], columns=values[0])
        
        # Convert date columns
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
        # Convert numeric columns - add error handling
        numeric_cols = ['totalUsers', 'activeUsers', 'sessions', 'bounceRate', 
                       'averageSessionDuration', 'screenPageViews', 'eventCount',
                       'screenPageViewsPerSession']  # Added this column
        for col in numeric_cols:
            if col in df.columns:
                # First try to convert directly, then clean strings if needed
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                
        return df
        
    except Exception as e:
        st.warning(f"Couldn't load {sheet_name} from Google Sheets")
        return pd.DataFrame()

# Social Media Data Loading Functions
def load_facebook_data(file_path):
    """Load Facebook data from CSV file"""
    try:
        if not os.path.exists(file_path):
            st.warning(f"Facebook data file not found: {file_path}")
            return pd.DataFrame()
            
        df = pd.read_csv(file_path)
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Convert date columns
        if 'Publish time' in df.columns:
            df['Publish time'] = pd.to_datetime(df['Publish time'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Error loading Facebook data: {e}")
        return pd.DataFrame()

def load_instagram_data(file_path):
    """Load Instagram data from CSV file"""
    try:
        if not os.path.exists(file_path):
            st.warning(f"Instagram data file not found: {file_path}")
            return pd.DataFrame()
            
        df = pd.read_csv(file_path)
        
        # Standardize column names
        df.columns = df.columns.str.strip()
        
        # Convert date columns
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Error loading Instagram data: {e}")
        return pd.DataFrame()

def load_linkedin_excel_data(file_path):
    """Load LinkedIn data from Excel file with more flexible sheet handling"""
    try:
        if not os.path.exists(file_path):
            st.warning(f"LinkedIn data file not found: {file_path}")
            return pd.DataFrame(), pd.DataFrame()
            
        xls = pd.ExcelFile(file_path)
        
        # Get all sheet names
        sheet_names = xls.sheet_names
        
        # Try to find metrics sheet (case insensitive)
        metrics_sheet = None
        posts_sheet = None
        
        for sheet in sheet_names:
            lower_sheet = sheet.lower()
            if 'metric' in lower_sheet:
                metrics_sheet = sheet
            elif 'post' in lower_sheet:
                posts_sheet = sheet
        
        # Load metrics data
        metrics_df = pd.DataFrame()
        if metrics_sheet:
            metrics_df = pd.read_excel(xls, sheet_name=metrics_sheet)
            if 'Date' in metrics_df.columns:
                metrics_df['Date'] = pd.to_datetime(metrics_df['Date'], errors='coerce')
        else:
            st.warning("No metrics sheet found in LinkedIn data")
        
        # Load posts data
        posts_df = pd.DataFrame()
        if posts_sheet:
            posts_df = pd.read_excel(xls, sheet_name=posts_sheet)
            # Handle different possible date column names
            date_cols = ['Created date', 'Post date', 'Date', 'Publish date']
            for col in date_cols:
                if col in posts_df.columns:
                    posts_df['date'] = pd.to_datetime(posts_df[col], errors='coerce')
                    break
        else:
            st.warning("No posts sheet found in LinkedIn data")
            
        return metrics_df, posts_df
        
    except Exception as e:
        st.error(f"Error loading LinkedIn data: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Metric Display Function
def display_metric(label, value, delta_value=0):
    delta_color = "green" if delta_value > 0 else "red" if delta_value < 0 else "gray"
    delta_sign = f"↑ {delta_value:.1f}%" if delta_value > 0 else f"↓ {abs(delta_value):.1f}%" if delta_value < 0 else ""
    
    st.markdown(f"""
        <div style="border: 1px solid #e1e4e8; border-radius: 5px; padding: 10px; margin: 5px;">
            <strong>{label}</strong><br>
            <span style="font-size: 24px;">{value}</span><br>
            <span style="color: {delta_color};">{delta_sign}</span>
        </div>
    """, unsafe_allow_html=True)

# Filter data by date range
def filter_data_by_date(data, start_date, end_date):
    if data is None or data.empty or 'date' not in data.columns:
        return data
    mask = (data['date'] >= pd.to_datetime(start_date)) & (data['date'] <= pd.to_datetime(end_date))
    return data.loc[mask]

# Page Functions
def page_overview(user_data, engagement_data):
    st.title("📊 Overview Dashboard")
    
    if not user_data.empty:
        st.header("User Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_users = user_data['totalUsers'].sum() if 'totalUsers' in user_data.columns else 0
            display_metric("Total Users", f"{total_users:,}")
        with col2:
            active_users = user_data['activeUsers'].sum() if 'activeUsers' in user_data.columns else 0
            display_metric("Active Users", f"{active_users:,}")
        with col3:
            sessions = user_data['sessions'].sum() if 'sessions' in user_data.columns else 0
            display_metric("Sessions", f"{sessions:,}")
        
        if 'activeUsers' in user_data.columns:
            fig = px.line(user_data, x='date', y='activeUsers', title='Active Users Over Time')
            st.plotly_chart(fig, use_container_width=True)
    
    if not engagement_data.empty:
        st.header("Engagement Metrics")
        col1, col2 = st.columns(2)
        with col1:
            avg_duration = engagement_data['averageSessionDuration'].mean() if 'averageSessionDuration' in engagement_data.columns else 0
            display_metric("Avg Session Duration", f"{avg_duration:.1f} sec")
        with col2:
            avg_pages = engagement_data['screenPageViewsPerSession'].mean() if 'screenPageViewsPerSession' in engagement_data.columns else 0
            display_metric("Pages/Session", f"{avg_pages:.1f}")
        
        if 'eventCount' in engagement_data.columns:
            fig = px.line(engagement_data, x='date', y='eventCount', title='Events Over Time')
            st.plotly_chart(fig, use_container_width=True)


def page_social_media(facebook_data, instagram_data, linkedin_metrics):
    st.title("📱 Social Media Analytics")
    
    if not facebook_data.empty:
        st.header("Facebook Performance")
        if 'Reach' in facebook_data.columns:
            display_metric("Total Reach", f"{facebook_data['Reach'].sum():,}")
        if 'Engaged users' in facebook_data.columns:
            display_metric("Engaged Users", f"{facebook_data['Engaged users'].sum():,}")
    
    if not instagram_data.empty:
        st.header("Instagram Performance")
        if 'Reach' in instagram_data.columns:
            display_metric("Total Reach", f"{instagram_data['Reach'].sum():,}")
        if 'Likes' in instagram_data.columns:
            display_metric("Total Likes", f"{instagram_data['Likes'].sum():,}")
    
    if not linkedin_metrics.empty:
        st.header("LinkedIn Performance")
        if 'Impressions (total)' in linkedin_metrics.columns:
            display_metric("Total Impressions", f"{linkedin_metrics['Impressions (total)'].sum():,}")

def filter_data_by_date(data, start_date, end_date):
    """Filter loaded data by date range"""
    if data is None or data.empty or 'date' not in data.columns:
        return data
    mask = (data['date'] >= pd.to_datetime(start_date)) & (data['date'] <= pd.to_datetime(end_date))
    return data.loc[mask]

def main():
    # Set default date range in dashboard
    default_start = datetime(2025, 2, 10).date()
    default_end = datetime.now().date()

    # Load data from Google Sheets (only existing sheets)
    user_data = get_sheet_data("user_traffic")
    engagement_data = get_sheet_data("engagement")
    
    # Load social media data
    facebook_data = load_facebook_data("social_media_data/Feb-01-2025_Mar-15-2025_613168031534769.csv")
    instagram_data = load_instagram_data("social_media_data/Feb-01-2025_Mar-15-2025_613168031534769.csv")
    linkedin_metrics, _ = load_linkedin_excel_data("social_media_data/pro-efficient-data-entry_content_1742193384396.xlsx")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Overview", "Social Media"])
    
    # Date selector in sidebar
    st.sidebar.header("Data Date Range")
    date_range = st.sidebar.date_input(
        "Select extraction date range",
        [default_start, default_end],
        min_value=default_start,
        max_value=default_end
    )
        
    # Filter displayed data by selected dates
    if len(date_range) == 2:
        filtered_user_data = filter_data_by_date(user_data, date_range[0], date_range[1])
        filtered_engagement_data = filter_data_by_date(engagement_data, date_range[0], date_range[1])
    else:
        filtered_user_data = user_data
        filtered_engagement_data = engagement_data

    # Display selected page
    if page == "Overview":
        page_overview(filtered_user_data, filtered_engagement_data)
    elif page == "Social Media":
        page_social_media(facebook_data, instagram_data, linkedin_metrics)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("Dashboard v1.0")

     # Refresh button that uses selected dates
    if st.sidebar.button("🔄 Refresh Data with Selected Dates"):
        start_date, end_date = date_range
        refresh_data(start_date, end_date)  # You'll need to modify data_extractor to accept these params
        st.rerun()

if __name__ == "__main__":
    main()