import streamlit as st
st.set_page_config(page_title="Digital Marketing & SEO Dashboard", layout="wide")

import sys
import pandas as pd
import subprocess
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from SEO_Files.seo_overview import page_overview
from SEO_Files.seo_acquisition import page_acquisition
from SEO_Files.seo_page_views import page_page_views
from SEO_Files.seo_demographics import page_demographics
from SEO_Files.seo_device_tech import page_device_technology
from SEO_Files.seo_events import page_events
from SEO_Files.seo_ecommerce import page_ecommerce
from SEO_Files.seo_ltv import page_ltv
from SEO_Files.seo_audience import page_audience
from SEO_Files.seo_app import page_app
from SEO_Files.seo_funnel import page_funnel
from SEO_Files.seo_retention import page_retention
from SEO_Files.seo_site_speed import page_site_speed
from SEO_Files.seo_error import page_error_tracking
from SEO_Files.seo_keyword import page_search_console
from SEO_Files.seo_metrics import page_seo_overview
from SMM_Files.smm_overview import page_smm_overview
from SMM_Files.smm_facebook import page_facebook
from SMM_Files.smm_instagram import page_instagram
from SMM_Files.smm_linkedin import page_linkedin_analysis
from SMM_Files.smm_youtube import page_youtube
from SMM_Files.smm_x import page_x
from SMM_Files.smm_calendar import show_social_media_calendar
from AI_Files.ai_insights import page_deepseek_ai
from Shared_Components.components import (
    display_metric,
    calculate_delta)
from Shared_Components.config import WORKSHEET_MAPPING
from data_loader import (
    connect_to_google_sheets,
    load_sheet_data,
    load_facebook_data,
    load_instagram_data,
    load_linkedin_data,
    load_youtube_data,
    load_x_data,
)


# Load data
SHEET_URL = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/17gv72J54TDcW9wSAtG0cKGXty0zxfgeKZVLEp65bYcc/edit?usp=sharing")

# Refreshing data extarction
def refresh_data():
    """Execute the data extraction script with proper error handling and progress indication"""
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()
    
    try:
        # Get the absolute paths
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        data_extraction_dir = project_root / "data_extraction"
        main_script = data_extraction_dir / "main.py"
        
        # Verify paths
        if not main_script.exists():
            status_text.error(f"Data extraction script not found at: {main_script}")
            progress_bar.empty()
            return False
            
        status_text.info("Starting data extraction...")
        progress_bar.progress(10)

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        # Run the script with progress updates
        status_text.info("Connecting to data sources...")
        progress_bar.progress(20)
        
        # Create a spinner while the subprocess runs
        with st.spinner("Extracting data from all sources..."):
            result = subprocess.run(
                        [sys.executable, str(main_script)],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',  # Explicitly set encoding
                        errors='replace',  # Replace un-decodable characters
                        env=env,
                        cwd=str(project_root))

            
            progress_bar.progress(70)
            status_text.info("Processing extracted data...")
            time.sleep(1)  # Simulate processing time
            
            # Display results
            output = f"Exit code: {result.returncode}\n\n"
            output += "=== STDOUT ===\n"
            output += result.stdout + "\n\n"
            output += "=== STDERR ===\n"
            output += result.stderr
            
            progress_bar.progress(90)
            status_text.info("Finalizing data refresh...")
            
            if result.returncode == 0:
                progress_bar.progress(100)
                status_text.success("Data refreshed successfully!")
                time.sleep(1)  # Let user see the success message
                st.cache_data.clear()  # Clear all caches
                progress_bar.empty()
                status_text.empty()
                st.rerun()  # Reload the app
                return True
            else:
                progress_bar.progress(100)
                status_text.error("Data refresh failed")
                st.sidebar.text_area("Extraction Log", output, height=300)
                progress_bar.empty()
                return False
                
    except Exception as e:
        progress_bar.progress(100)
        status_text.error(f"Refresh error: {str(e)}")
        progress_bar.empty()
        return False
    
# Add this function in your dashboard.py
def get_date_range_filter():
    """Create date range filter widget"""
    today = datetime.now()
    default_start = today - timedelta(days=30)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=default_start)
    with col2:
        end_date = st.date_input("End date", value=today)
    
    return start_date, end_date

def clean_dataframe(df):
    """Comprehensive data cleaning for all numeric columns"""
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
        
    # Identify numeric columns (adjust as needed)
    numeric_cols = ['activeUsers', 'sessions', 'users', 'pageviews'] 
    
    for col in numeric_cols:
        if col in df.columns:
            # Multi-step cleaning process
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r'[^\d.]', '', regex=True)
                .replace('', '0')
                .astype(float)
            )
    return df

def main():
    # Navigation
    st.sidebar.title("Navigation")
    start_date, end_date = get_date_range_filter()

    try:
        with st.spinner("Loading dashboard data..."):
            gc = connect_to_google_sheets()
            if gc is None:
                st.error("Failed to connect to Google Sheets. Using cached data if available.")
                all_data = {}
            else:
                with st.spinner("Fetching data from Google Sheets..."):
                    # Pass both required arguments
                    all_data = load_sheet_data(gc, SHEET_URL)  # <-- This is the fixed line
                    
                    if not all_data:
                        st.warning("No data loaded from Google Sheets")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        all_data = {}

    # Map data to variables with date filtering
    def filter_data(df):
        """Filter data with basic validation"""
        # Handle None case
        if df is None:
            return pd.DataFrame()
            
        # Handle tuple case
        if isinstance(df, tuple):
            return tuple(filter_data(d) for d in df)
        
        # Handle DataFrame case
        if isinstance(df, pd.DataFrame):
            if df.empty:
                return df
            
            # Existing date filtering logic
            date_col = None
            for col in df.columns:
                if any(x in col.lower() for x in ['date', 'time', 'created', 'published']):
                    date_col = col
                    break
                    
            if date_col:
                try:
                    df[date_col] = pd.to_datetime(df[date_col])
                    mask = (df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))
                    return df.loc[mask]
                except Exception as e:
                    st.error(f"Error filtering {date_col}: {e}")
            return df
        
        # For any other type, return empty DataFrame
        return pd.DataFrame()



    # Map data to variables
    user_traffic_data = filter_data(all_data.get("user_traffic", pd.DataFrame()))
    engagement_data = filter_data(all_data.get("engagement", pd.DataFrame()))
    acquisition_data = filter_data(all_data.get("acquisition", pd.DataFrame()))
    page_views_data = filter_data(all_data.get("page_views", pd.DataFrame()))
    demographics_data = filter_data(all_data.get("demographics", pd.DataFrame()))
    device_data = filter_data(all_data.get("technology", pd.DataFrame()))
    events_data = filter_data(all_data.get("events", pd.DataFrame()))
    site_speed_data = filter_data(all_data.get("site_speed", pd.DataFrame()))
    search_console_data = filter_data(all_data.get("seo_top_queries", pd.DataFrame()))
    seo_pages_data = filter_data(all_data.get("seo_top_pages", pd.DataFrame()))
    seo_content_data = filter_data(all_data.get("seo_content_engagement", pd.DataFrame()))
    organic_search_data = filter_data(all_data.get("organic_search", pd.DataFrame()))
    landing_pages_data = filter_data(all_data.get("seo_landing_pages", pd.DataFrame()))
    audience_data = filter_data(all_data.get("audience_segments", pd.DataFrame()))


    conversion_data = pd.DataFrame(columns=["date", "conversions", "totalRevenue"])
    ecommerce_data = pd.DataFrame(columns=["date", "productName", "itemRevenue"])
    ltv_data = pd.DataFrame(columns=["date", "userLifetimeBucket", "userLifetimeRevenue"])
    app_data = pd.DataFrame(columns=["date", "appVersion", "userEngagementDuration"])
    funnel_data = pd.DataFrame(columns=["date", "funnelStep", "funnelConversions"])
    retention_data = pd.DataFrame(columns=["date", "cohort", "retentionRate"])
    error_data = pd.DataFrame(columns=["date", "eventName", "eventCount"])
    ga4_data = pd.DataFrame(columns=["date", "sessions", "users"])
    seo_data = pd.DataFrame(columns=["Date", "Keyword", "Position"])

    # Load social media data
    facebook_data = filter_data(load_facebook_data())
    instagram_data = filter_data(load_instagram_data())
    linkedin_metrics, linkedin_posts = load_linkedin_data()
    linkedin_metrics = filter_data(linkedin_metrics)
    linkedin_posts= filter_data(linkedin_posts)
    youtube_data = filter_data(load_youtube_data())
    x_data = filter_data(load_x_data())

    youtube_data = pd.DataFrame(columns=["Date", "Title", "Views"])
    x_data = pd.DataFrame(columns=["Date", "Tweet", "Impressions"])

    section = st.sidebar.radio("Select Section", ["Search Engine Optimization (SEO)", "Social Media Management (SMM)", "AI Insights"])

    if section == "Search Engine Optimization (SEO)":
        page = st.sidebar.radio(
            "Go to",
            [
                "Overview", "Acquisition", "Page Views", "Demographics", "Device & Technology",
                "Events", "E-commerce", "User Lifetime Value", "Audience & Segments", "App-Specific Data",
                "Funnel Analysis", "Retention & Cohorts", "Site Speed & Performance", "Error Tracking",
                "Keyword Analysis", "SEO Metrics Overview"
            ]
        )

        if page == "Overview":
            page_overview(user_traffic_data, engagement_data, conversion_data)
        elif page == "Acquisition":
            page_acquisition(acquisition_data)
        elif page == "Page Views":
            page_page_views(page_views_data)
        elif page == "Demographics":
            page_demographics(demographics_data)
        elif page == "Device & Technology":
            page_device_technology(device_data)
        elif page == "Events":
            page_events(events_data)
        elif page == "E-commerce":
            page_ecommerce(ecommerce_data)
        elif page == "User Lifetime Value":
            page_ltv(ltv_data)
        elif page == "Audience & Segments":
            page_audience(audience_data)
        elif page == "App-Specific Data":
            page_app(app_data)
        elif page == "Funnel Analysis":
            page_funnel(funnel_data)
        elif page == "Retention & Cohorts":
            page_retention(retention_data)
        elif page == "Site Speed & Performance":
            page_site_speed(site_speed_data)
        elif page == "Error Tracking":
            page_error_tracking(error_data)
        elif page == "Keyword Analysis":
            page_search_console(search_console_data)
        elif page == "SEO Metrics Overview":
            page_seo_overview(search_console_data, ga4_data, seo_data)

    elif section == "Social Media Management (SMM)":
        page = st.sidebar.radio(
            "Choose Platform",
            [
                "Overview", "Facebook", "Instagram", "LinkedIn Analysis", 
                "YouTube", "X (Twitter)", "Calendar"
            ]
        )

        if page == "Overview":
            page_smm_overview(facebook_data, instagram_data, linkedin_metrics, linkedin_posts, youtube_data, x_data)
        elif page == "Facebook":
            page_facebook(facebook_data)
        elif page == "Instagram":
            page_instagram(instagram_data)
        elif page == "LinkedIn Analysis":
            page_linkedin_analysis(linkedin_metrics, linkedin_posts)
        elif page == "YouTube":
            page_youtube(youtube_data)
        elif page == "X (Twitter)":
            page_x(x_data)
        elif page == "Calendar":
            show_social_media_calendar(facebook_data, instagram_data, linkedin_posts)

    elif section == "AI Insights":
        page_deepseek_ai(
            user_traffic_data, conversion_data, demographics_data,
            device_data, events_data, ecommerce_data, ltv_data,
            audience_data, app_data, funnel_data, retention_data,
            site_speed_data, error_data
        )

    # Add refresh button at the top of the sidebar
    st.sidebar.title("Data Control")
    if st.sidebar.button("🔄 Refresh Data", help="Fetch fresh data from all sources"):
        with st.spinner("Refreshing data from sources..."):
            if refresh_data():
                st.success("Data refresh completed successfully!")
            else:
                st.error("Data refresh encountered problems")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        **Digital Marketing & SEO Dashboard**  
        Built with ❤️ using **Streamlit**
    """)

if __name__ == "__main__":
    main()