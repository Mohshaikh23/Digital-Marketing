from github import Github
import base64
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.api_core.exceptions import PermissionDenied
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2 import service_account
import requests
import logging
import json
from datetime import datetime, timedelta

# Configure logging to show only ERROR messages
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Define the scopes for Google Search Console API
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly', 'https://www.googleapis.com/auth/analytics.readonly']

# credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# if credentials_path and os.path.exists(credentials_path):
#     client = BetaAnalyticsDataClient.from_service_account_file(credentials_path)
# else:
#     raise FileNotFoundError("⚠️ Service account JSON file not found. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable.")

# # Path to your service account JSON key file
# SERVICE_ACCOUNT_FILE = 'proefficient-data-entry-194479023ae8.json'

# Google Analytics Property ID (e.g., 'properties/123456789')
PROPERTY_ID = "properties/477624929"

# File to save the data
OUTPUT_DIR = "analytics_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# # Authenticate using the service account
# creds = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def push_to_github(repo_name, file_path, file_content, commit_message, github_token):
    """
    Push a file to a GitHub repository.
    
    :param repo_name: Name of the repository (e.g., "Mohshaikh23/Digital-Marketing")
    :param file_path: Path to the file in the repository (e.g., "analytics_data/user_traffic_data.csv")
    :param file_content: Content of the file to be pushed
    :param commit_message: Commit message
    :param github_token: GitHub personal access token
    """
    try:
        # Initialize GitHub instance
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        # Check if the file already exists
        try:
            file = repo.get_contents(file_path)
            # If the file exists, update it
            repo.update_file(file_path, commit_message, file_content, file.sha)
        except:
            # If the file does not exist, create it
            repo.create_file(file_path, commit_message, file_content)
        
        print(f"Successfully pushed {file_path} to GitHub.")
    except Exception as e:
        print(f"Failed to push {file_path} to GitHub: {e}")

# Initialize the client
def initialize_client():
    try:
        # ✅ Debugging: Check if Streamlit Secrets are available
        if "google" not in st.secrets or "credentials" not in st.secrets["google"]:
            raise ValueError("❌ Streamlit Secrets are missing. Ensure they are set in Streamlit Cloud.")

        credentials_info = st.secrets["google"]["credentials"]
        credentials_dict = json.loads(credentials_info)

        # ✅ Debugging: Print project ID to verify credentials loaded correctly
        st.write(f"✅ Project ID: {credentials_dict.get('project_id', 'Not found')}")

        creds = service_account.Credentials.from_service_account_info(credentials_dict)
        client = BetaAnalyticsDataClient(credentials=creds)

        st.success("✅ Google Analytics Client Initialized Successfully!")
        return client
    except Exception as e:
        st.error(f"⚠️ Failed to initialize Google Analytics client: {e}")
        return None

creds = service_account.Credentials.from_service_account_info(json.loads(st.secrets["google"]["credentials"]))

# Debugging: Check if secrets are accessible
if "google" in st.secrets and "credentials" in st.secrets["google"]:
    st.write("✅ Streamlit Secrets are available.")
else:
    st.error("❌ Streamlit Secrets are missing or not set properly.")

# Function to authenticate and get credentials
def authenticate_google_apis():
    """
    Authenticate with Google APIs using credentials from Streamlit Secrets.
    """
    creds = None

    # Load credentials from Streamlit Secrets
    if "google" in st.secrets:
        google_secrets = st.secrets["google"]
        client_config = {
            "web": {
                "client_id": google_secrets["client_id"],
                "client_secret": google_secrets["client_secret"],
                "project_id": google_secrets["project_id"],
                "auth_uri": google_secrets["auth_uri"],
                "token_uri": google_secrets["token_uri"],
                "auth_provider_x509_cert_url": google_secrets["auth_provider_x509_cert_url"],
            }
        }
    else:
        raise ValueError("Google API credentials not found in Streamlit Secrets.")

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=8080)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

# Function to fetch data from Google Search Console
def fetch_search_console_data(creds, site_url, start_date, end_date):
    service = build('searchconsole', 'v1', credentials=creds)
    
    request = {
        'startDate': start_date,
        'endDate': datetime.today().strftime('%Y-%m-%d'),
        'dimensions': ['query', 'page', 'device'],  # Get data by query, page, and device
        'rowLimit': 10000  # Maximum number of rows to fetch
    }
    
    response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
    
    if 'rows' not in response:
        print("No data found.")
        return None
    
    rows = response['rows']
    data = []
    for row in rows:
        query = row['keys'][0]  # Keyword
        page = row['keys'][1]   # Page URL
        device = row['keys'][2]  # Device type
        clicks = row['clicks']
        impressions = row['impressions']
        ctr = row['ctr']
        position = row['position']
        data.append([query, page, device, clicks, impressions, ctr, position])
    
    return pd.DataFrame(data, columns=['Query', 'Page', 'Device', 'Clicks', 'Impressions', 'CTR', 'Position'])


# Function to fetch data from Google Analytics 4
def fetch_ga4_data(creds, property_id, start_date, end_date):
    service = build('analyticsdata', 'v1beta', credentials=creds)
    request = {
        'dateRanges': [{'startDate': start_date, 'endDate': end_date}],
        'dimensions': [{'name': 'pagePath'}, {'name': 'deviceCategory'}],
        'metrics': [{'name': 'sessions'}, {'name': 'averageSessionDuration'}, {'name': 'screenPageViewsPerSession'}]
    }
    response = service.properties().batchRunReports(property=property_id, body=request).execute()
    rows = response.get('reports', [])[0].get('rows', [])
    data = []
    for row in rows:
        page = row['dimensionValues'][0]['value']
        device = row['dimensionValues'][1]['value']
        sessions = row['metricValues'][0]['value']
        avg_session_duration = row['metricValues'][1]['value']
        pages_per_session = row['metricValues'][2]['value']
        data.append([page, device, sessions, avg_session_duration, pages_per_session])
    return pd.DataFrame(data, columns=['Page', 'Device', 'Sessions', 'AvgSessionDuration', 'PagesPerSession'])

# Function to fetch third-party SEO data (e.g., Ahrefs, SEMrush)
def fetch_seo_data(api_key):
    # Example: Fetch backlinks and domain authority from Ahrefs API
    url = f"https://api.ahrefs.com/v3/site-explorer/backlinks?target=example.com&mode=domain&limit=1000&token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        backlinks = data['metrics']['backlinks']
        domain_authority = data['metrics']['domain_rating']
        return backlinks, domain_authority
    else:
        return None, None

# Function to authenticate and get credentials for Google Search Console
def authenticate_google_search_console():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8081)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# Function to save data to a file
def save_data(data, filename, github_token=None):
    """
    Save data to a local file and optionally push it to GitHub.
    
    :param data: DataFrame to save
    :param filename: Name of the file to save
    :param github_token: GitHub personal access token (optional)
    """
    if data is not None and not data.empty:
        # Save data locally
        local_path = os.path.join(OUTPUT_DIR, filename)
        data.to_csv(local_path, index=False)
        print(f"Data saved to {local_path}")
        
        # Push to GitHub if token is provided
        if github_token:
            repo_name = "Mohshaikh23/Digital-Marketing"
            file_path = f"analytics_data/{filename}"
            with open(local_path, "r") as file:
                file_content = file.read()
            push_to_github(repo_name, file_path, file_content, f"Update {filename}", github_token)
    else:
        print(f"No data to save for {filename}.")


def fetch_data(client, dimensions, metrics, date_ranges, filename):
    try:
        request = RunReportRequest(
            property=PROPERTY_ID,
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[Metric(name=metric) for metric in metrics],
            date_ranges=[DateRange(start_date=date_range[0], end_date=date_range[1]) for date_range in date_ranges],
        )
        response = client.run_report(request)

        if not response.rows:
            print(f"⚠️ No data returned for {filename}. Skipping file creation.")
            return None  # Return None instead of saving empty files

        rows = []
        for row in response.rows:
            row_data = {dim: row.dimension_values[i].value for i, dim in enumerate(dimensions)}
            row_data.update({metric: row.metric_values[i].value for i, metric in enumerate(metrics)})
            rows.append(row_data)

        return pd.DataFrame(rows)
    except Exception as e:
        print(f"⚠️ Error fetching data: {e}")
        return None


def load_linkedin_excel_data(filename):
    """
    Load and preprocess LinkedIn data from an Excel file.
    """
    try:
        # Load the Excel file
        linkedin_data = pd.read_excel(filename, sheet_name=None)
        
        # Preprocess the 'Metrics' sheet
        metrics_df = None
        if 'Metrics' in linkedin_data:
            metrics_df = linkedin_data['Metrics']
            # Rename columns to ensure consistency
            metrics_df.columns = metrics_df.columns.str.strip()  # Remove leading/trailing spaces
            # Convert 'Date' column to datetime
            if 'Date' in metrics_df.columns:
                metrics_df['Date'] = pd.to_datetime(metrics_df['Date'], errors='coerce')
            # Drop rows with all zeros (if any)
            metrics_df = metrics_df.loc[(metrics_df.iloc[:, 1:] != 0).any(axis=1)]
        
        # Preprocess the 'All posts' sheet
        posts_df = None
        if 'All posts' in linkedin_data:
            posts_df = linkedin_data['All posts']
            # Rename columns to ensure consistency
            posts_df.columns = posts_df.columns.str.strip()  # Remove leading/trailing spaces
            # Convert 'Created date' column to datetime
            if 'Created date' in posts_df.columns:
                posts_df['Created date'] = pd.to_datetime(posts_df['Created date'], errors='coerce')
            # Drop rows with missing or invalid data
            posts_df = posts_df.dropna(subset=['Post title', 'Post link'])
        
        return metrics_df, posts_df
    except Exception as e:
        print(f"Error loading LinkedIn Excel file: {e}")
        return None, None

# Main function to fetch and save all data
def main():

    # Initialize GitHub token (replace with your actual token or use an environment variable)
    github_token = os.getenv("GITHUB_TOKEN")  # Replace with your GitHub token

    client = initialize_client()
    if not client:
        return

    creds = authenticate_google_apis()
    site_url = 'https://proefficientdataentry.com/'  # Replace with your website URL
    property_id = PROPERTY_ID  # Replace with your GA4 property ID
    start_date = '2025-02-10'  # Replace with your start date
    end_date = datetime.today().strftime('%Y-%m-%d')

    # Define date ranges starting from February 10, 2025
    date_ranges = [("2025-02-10", "today")]

    # 1. User & Traffic Data (Daily)
    logging.info("Fetching User & Traffic Data (Daily)...")
    user_traffic_data = fetch_data(
        client,
        dimensions=["date"],  # Ensure daily data by including the 'date' dimension
        metrics=["sessions", "totalUsers", "activeUsers", "screenPageViews", "bounceRate"],
        date_ranges=date_ranges,
        filename="user_traffic_data.csv"
    )
    save_data(user_traffic_data, "user_traffic_data.csv",github_token)

    # 2. User Engagement & Behavior (Daily)
    logging.info("Fetching User Engagement & Behavior Data (Daily)...")
    engagement_data = fetch_data(
        client,
        dimensions=["date"],  # Ensure daily data by including the 'date' dimension
        metrics=["averageSessionDuration", "screenPageViewsPerSession", "eventCount"],
        date_ranges=date_ranges,
        filename="engagement_data.csv"
    )
    save_data(engagement_data, "engagement_data.csv",github_token)

    # 3. Acquisition Data (Daily)
    logging.info("Fetching Acquisition Data (Daily)...")
    acquisition_data = fetch_data(
        client,
        dimensions=["date", "sessionSource", "sessionMedium"],  # Ensure daily data by including the 'date' dimension
        metrics=["sessions", "totalUsers"],
        date_ranges=date_ranges,
        filename="acquisition_data.csv"
    )
    save_data(acquisition_data, "acquisition_data.csv",github_token)

    # 4. Conversion & Goal Tracking (Daily)
    logging.info("Fetching Conversion & Goal Tracking Data (Daily)...")
    conversion_data = fetch_data(
        client,
        dimensions=["date"],  # Ensure daily data by including the 'date' dimension
        metrics=["conversions", "totalRevenue"],
        date_ranges=date_ranges,
        filename="conversion_data.csv"
    )
    save_data(conversion_data, "conversion_data.csv",github_token)

    # 5. Page Views Data (Daily)
    logging.info("Fetching Page Views Data (Daily)...")
    page_views_data = fetch_data(
        client,
        dimensions=["date", "pagePath", "pageTitle"],  # Include page-specific dimensions
        metrics=["screenPageViews"],  # Metric for page views
        date_ranges=date_ranges,
        filename="page_views_data.csv"
    )
    save_data(page_views_data, "page_views_data.csv",github_token)

    # 6. Demographics Data (Daily)
    logging.info("Fetching Demographics Data (Daily)...")
    demographics_data = fetch_data(
        client,
        dimensions=["date", "userAgeBracket", "userGender","country"],  # Valid dimensions
        metrics=["activeUsers"],  # Valid metric
        date_ranges=date_ranges,
        filename="demographics_data.csv"
    )
    save_data(demographics_data, "demographics_data.csv",github_token)

    # 7. Device & Technology Data (Daily)
    logging.info("Fetching Device & Technology Data (Daily)...")
    device_data = fetch_data(
        client,
        dimensions=["date", "deviceCategory", "operatingSystem", "browser"],
        metrics=["sessions", "activeUsers"],
        date_ranges=date_ranges,
        filename="device_data.csv"
    )
    save_data(device_data, "device_data.csv",github_token)

    # 8. Events Data (Daily)
    logging.info("Fetching Events Data (Daily)...")
    events_data = fetch_data(
        client,
        dimensions=["date", "eventName"],
        metrics=["eventCount"],
        date_ranges=date_ranges,
        filename="events_data.csv"
    )
    save_data(events_data, "events_data.csv",github_token)

    # 9. E-commerce Data (Daily)
    logging.info("Fetching E-commerce Data (Daily)...")
    ecommerce_data = fetch_data(
        client,
        dimensions=["date", "productName", "productCategory"],
        metrics=["itemRevenue", "itemsPurchased"],
        date_ranges=date_ranges,
        filename="ecommerce_data.csv"
    )
    save_data(ecommerce_data, "ecommerce_data.csv",github_token)

    # 10. User Lifetime Value (LTV) Data (Daily)
    logging.info("Fetching User Lifetime Value Data (Daily)...")
    ltv_data = fetch_data(
        client,
        dimensions=["date", "userLifetimeBucket"],
        metrics=["userLifetimeRevenue", "userLifetimeTransactions"],
        date_ranges=date_ranges,
        filename="ltv_data.csv"
    )
    save_data(ltv_data, "ltv_data.csv",github_token)

    # 11. Audience & Segments Data (Daily)
    logging.info("Fetching Audience & Segments Data (Daily)...")
    audience_data = fetch_data(
        client,
        dimensions=["date", "audienceName"],  # Use audienceName instead of segment
        metrics=["activeUsers", "conversions"],
        date_ranges=date_ranges,
        filename="audience_data.csv"
    )
    save_data(audience_data, "audience_data.csv",github_token)

    # 12. App-Specific Data (Daily)
    logging.info("Fetching App-Specific Data (Daily)...")
    app_data = fetch_data(
        client,
        dimensions=["date", "appVersion", "platform"],
        metrics=["screenPageViews", "userEngagementDuration"],  # Use screenPageViews
        date_ranges=date_ranges,
        filename="app_data.csv"
    )
    save_data(app_data, "app_data.csv",github_token)


    # 13. Funnel Analysis Data (Daily)
    logging.info("Fetching Funnel Analysis Data (Daily)...")
    funnel_data = fetch_data(
        client,
        dimensions=["date", "eventName", "pagePath"],
        metrics=["funnelConversions", "funnelDropOffRate"],
        date_ranges=date_ranges,
        filename="funnel_data.csv"
    )
    save_data(funnel_data, "funnel_data.csv",github_token)

    # 14. Retention & Cohorts Data (Daily)
    logging.info("Fetching Retention & Cohorts Data (Daily)...")
    retention_data = fetch_data(
        client,
        dimensions=["date", "cohort", "cohortNthDay"],
        metrics=["activeUsers"],
        date_ranges=date_ranges,
        filename="retention_data.csv"
    )
    save_data(retention_data, "retention_data.csv",github_token)

    # 15. Site Speed & Performance Data (Daily)
    logging.info("Fetching Site Speed & Performance Data (Daily)...")
    site_speed_data = fetch_data(
        client,
        dimensions=["date", "pagePath", "eventName"],  # Include eventName
        metrics=["averageSessionDuration"],  # Valid metric
        date_ranges=date_ranges,
        filename="site_speed_data.csv"
    )
    save_data(site_speed_data, "site_speed_data.csv",github_token)


    # 16. Error Tracking Data (Daily)
    logging.info("Fetching Error Tracking Data (Daily)...")
    error_data = fetch_data(
        client,
        dimensions=["date", "pagePath", "eventName"],  # Track custom error events
        metrics=["eventCount"],  # Count of error events
        date_ranges=date_ranges,
        filename="error_data.csv"
    )
    save_data(error_data, "error_data.csv",github_token)

    # 17. Google Search Console Data (Daily)
    logging.info("Fetching Google Search Console Data (Daily)...")
    creds = authenticate_google_search_console()
    site_url = 'https://proefficientdataentry.com/'  # Replace with your website URL
    start_date = '2025-02-10'  # Replace with your start date
    end_date = datetime.today().strftime('%Y-%m-%d')

    # Fetch search analytics data
    search_console_data = fetch_search_console_data(creds, site_url, start_date, end_date)
    
    if search_console_data is not None:
        # Save the data to a CSV file
        search_console_data.to_csv('analytics_data/search_console_data.csv', index=False)
        logging.info("Search Console data saved to 'analytics_data/search_console_data.csv'")
    else:
        logging.error("No data fetched from Google Search Console.")

    # Fetch data from Google Analytics 4
    logging.info("Fetching Google Analytics 4 data...")
    ga4_data = fetch_ga4_data(creds, property_id, start_date, end_date)
    ga4_data.to_csv('analytics_data/ga4_data.csv', index=False)

    # Fetch third-party SEO data (e.g., Ahrefs)
    logging.info("Fetching third-party SEO data...")
    api_key = 'your_api_key'  # Replace with your API key
    backlinks, domain_authority = fetch_seo_data(api_key)
    seo_data = pd.DataFrame({'Backlinks': [backlinks], 'DomainAuthority': [domain_authority]})
    seo_data.to_csv('analytics_data/seo_data.csv', index=False)

if __name__ == "__main__":
    main()