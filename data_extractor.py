import os
import json
from datetime import datetime, timedelta
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, FilterExpression, Filter
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import numpy as np

# Configuration
SPREADSHEET_ID = "17gv72J54TDcW9wSAtG0cKGXty0zxfgeKZVLEp65bYcc"
SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/youtube.readonly'
]
OUTPUT_DIR = "analytics_data"
SEARCH_CONSOLE_SITE_URL = "https://proefficientdataentry.com/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SEO Data Sources Configuration
SEO_DATA_SOURCES = [
    # User Metrics
    {
        "name": "User Traffic",
        "filename": "user_traffic.csv",
        "dimensions": ["date"],
        "metrics": ["totalUsers", "activeUsers", "newUsers", "sessions", "bounceRate"]
    },
    
    # Engagement
    {
        "name": "User Engagement",
        "filename": "engagement.csv",
        "dimensions": ["date"],
        "metrics": ["averageSessionDuration", "screenPageViewsPerSession", "eventCount"]
    },
    
    # Acquisition
    {
        "name": "Acquisition",
        "filename": "acquisition.csv",
        "dimensions": ["date", "sessionSource", "sessionMedium"],
        "metrics": ["sessions", "totalUsers", "engagedSessions"]
    },
    
    # Page Performance
    {
        "name": "Page Views",
        "filename": "page_views.csv",
        "dimensions": ["date", "pagePath", "pageTitle"],
        "metrics": ["screenPageViews", "screenPageViewsPerSession"]
    },
   # User Demographics (simplified)
    {
        "name": "User Demographics",
        "filename": "demographics.csv",
        "dimensions": ["date", "userAgeBracket", "userGender"],
        "metrics": ["activeUsers", "newUsers", "sessions", "engagedSessions"]
    },

    # Acquisition Demographics (optional separate request)
    {
        "name": "Acquisition Demographics",
        "filename": "acquisition_demographics.csv",
        "dimensions": ["date", "firstUserSource", "firstUserMedium"],
        "metrics": ["activeUsers", "newUsers", "sessions"]
    },

    # Conversions
    {
        "name": "Conversions",
        "filename": "conversions.csv",
        "dimensions": ["date"],
        "metrics": ["conversions", "totalRevenue"]
    },

    # Technology/Device
    {
        "name": "Technology",
        "filename": "technology.csv",
        "dimensions": ["date", "deviceCategory", "operatingSystem", "browser"],
        "metrics": ["activeUsers", "sessions"]
    },

    # Events
    {
        "name": "Events",
        "filename": "events.csv",
        "dimensions": ["date", "eventName"],
        "metrics": ["eventCount"]
    },
    
    # SEO-Specific Sources
    {
        "name": "SEO Landing Pages",
        "filename": "seo_landing_pages.csv",
        "dimensions": ["date", "landingPage", "sessionSource", "sessionMedium"],
        "metrics": ["sessions", "engagedSessions", "averageSessionDuration", "bounceRate"]
    },
    
    {
        "name": "Organic Search Performance",
        "filename": "organic_search.csv",
        "dimensions": ["date", "firstUserSource", "firstUserMedium"],
        "metrics": ["sessions", "totalUsers", "conversions", "engagementRate"]
    },
    
    {
    "name": "Site Speed Metrics",
    "filename": "site_speed.csv",
    "dimensions": ["date", "pagePath"],
    "metrics": [
        "screenPageViews",
        "userEngagementDuration", 
        "eventCount",
        "averageSessionDuration"
    ],
    "calculated_metrics": [
        {
            "name": "avgEngagementPerView",
            "expression": "userEngagementDuration/screenPageViews",
            "format": "FLOAT"
        },
        {
            "name": "eventsPerView",
            "expression": "eventCount/screenPageViews",
            "format": "FLOAT"
        }
    ],
    "filter": "eventCount>0"  # Only include pages with engagement
    },
    
    {
        "name": "Internal Search Terms",
        "filename": "internal_search.csv",
        "dimensions": ["date", "searchTerm"],
        "metrics": ["eventCount", "sessions"],
        "filter": "eventName==search"
    },
    
    {
        "name": "Content Engagement",
        "filename": "content_engagement.csv",
        "dimensions": ["date", "pageTitle", "pagePath"],
        "metrics": ["screenPageViews", "screenPageViewsPerSession", "totalUsers", "engagementRate"]
    }
]

def initialize_services():
    """Initialize Google services with proper authentication"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        sheets_service = build('sheets', 'v4', credentials=creds)
        analytics_client = BetaAnalyticsDataClient(credentials=creds)
        
        print("✅ Analytics and Sheets services initialized")
        return sheets_service, analytics_client
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return None, None

def get_sheet_id(sheets_service, sheet_name):
    """Get numeric sheet ID from sheet name"""
    try:
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID,
            fields="sheets(properties(title,sheetId))"
        ).execute()
        
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        return create_sheet(sheets_service, sheet_name)
        
    except Exception as e:
        print(f"⚠️ Error getting sheet ID: {e}")
        return None

def create_sheet(sheets_service, sheet_name):
    """Create new sheet and return its ID"""
    try:
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'frozenRowCount': 1,
                            'rowCount': 1000,
                            'columnCount': 20
                        },
                        'tabColor': {
                            'red': 0.2,
                            'green': 0.6,
                            'blue': 0.8
                        }
                    }
                }
            }]
        }
        result = sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        return result['replies'][0]['addSheet']['properties']['sheetId']
        
    except Exception as e:
        print(f"⚠️ Error creating sheet: {e}")
        return None

def save_data(data, filename, sheets_service):
    """Save data to local CSV and Google Sheet"""
    try:
        if data is None or data.empty:
            print("⚠️ No data to save")
            return False
            
        sheet_name = os.path.splitext(filename)[0]
        local_path = os.path.join(OUTPUT_DIR, filename)
        
        # Save locally
        data.to_csv(local_path, index=False)
        print(f"📁 Local save: {local_path}")
        
        # Prepare Google Sheets update
        sheet_id = get_sheet_id(sheets_service, sheet_name)
        if sheet_id is None:
            return False
            
        values = [data.columns.tolist()] + data.values.tolist()
        
        # Clear existing data
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:Z",
        ).execute()
        
        # Update with new data
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': values}
        ).execute()
        
        # Apply formatting
        try:
            format_body = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
                                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    },
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': sheet_id,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': len(data.columns)
                            }
                        }
                    }
                ]
            }
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body=format_body
            ).execute()
        except Exception as e:
            print(f"⚠️ Formatting skipped: {e}")
        
        print(f"📊 Updated {sheet_name} ({result['updatedCells']} cells)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save {filename}: {e}")
        return False

def fetch_analytics_data(client, dimensions, metrics, date_ranges, filter_expression=None):
    """Fetch data from Google Analytics with enforced date range"""
    try:
        # Ensure date_ranges is properly formatted
        if not isinstance(date_ranges, list):
            date_ranges = [date_ranges]
        
        # Create DateRange objects directly from input
        date_range_objects = [
            DateRange(start_date=start, end_date=end)
            for start, end in date_ranges
        ]
        
        request = RunReportRequest(
            property="properties/477624929",
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[Metric(name=metric) for metric in metrics],
            date_ranges=date_range_objects,
        )

        if filter_expression:
            if "==" in filter_expression:
                field, value = filter_expression.split("==")
                request.dimension_filter = FilterExpression(
                    filter=Filter(
                        field_name=field.strip(),
                        string_filter=Filter.StringFilter(
                            match_type="EXACT",
                            value=value.strip('"\' ')
                        )
                    )
                )
        
        response = client.run_report(request)
        
        if not response.rows:
            print("⚠️ No data returned from Analytics API")
            return None
            
        # Convert to DataFrame
        rows = []
        for row in response.rows:
            row_data = {}
            for i, dim in enumerate(dimensions):
                val = row.dimension_values[i].value
                if dim == "date":
                    val = datetime.strptime(val, "%Y%m%d").strftime("%Y-%m-%d")
                row_data[dim] = val
                
            for i, metric in enumerate(metrics):
                try:
                    row_data[metric] = float(row.metric_values[i].value)
                except:
                    row_data[metric] = row.metric_values[i].value
                    
            rows.append(row_data)
            
        df = pd.DataFrame(rows)
        return df[dimensions + metrics]
        
    except Exception as e:
        print(f"❌ Analytics API error: {e}")
        return None

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

def generate_seo_report(analytics_client, search_console_site_url):
    """Generate comprehensive SEO report"""
    print("\n🔍 Generating Comprehensive SEO Report...")
    
    # 1. Get Search Console Data
    sc_data = fetch_search_console_data(search_console_site_url)
    
    # 2. Get Analytics Data for SEO
    seo_data = {}
    for source in [s for s in SEO_DATA_SOURCES if s['name'] in [
        'SEO Landing Pages', 
        'Organic Search Performance',
        'Content Engagement'
    ]]:
        data = fetch_analytics_data(
            client=analytics_client,
            dimensions=source["dimensions"],
            metrics=source["metrics"],
            date_ranges=[("30daysAgo", "today")],
            filter_expression=source.get("filter")
        )
        seo_data[source['name']] = data
    
    # 3. Process and combine data
    reports = {}
    
    if not sc_data.empty:
        reports['top_queries'] = (
            sc_data.groupby('query')
            .agg({
                'clicks': 'sum',
                'impressions': 'sum',
                'position': 'mean',
                'ctr': 'mean'
            })
            .sort_values('clicks', ascending=False)
            .head(50)
        )
        
        reports['top_pages'] = (
            sc_data.groupby('page')
            .agg({
                'clicks': 'sum',
                'impressions': 'sum',
                'position': 'mean'
            })
            .sort_values('clicks', ascending=False)
            .head(50)
        )
    
    if 'Content Engagement' in seo_data and not seo_data['Content Engagement'].empty:
        reports['content_engagement'] = (
            seo_data['Content Engagement']
            .groupby('pagePath')
            .agg({
                'screenPageViews': 'sum',
                'engagementRate': 'mean'
            })
            .sort_values('screenPageViews', ascending=False)
            .head(50)
        )
    
    if 'Organic Search Performance' in seo_data and not seo_data['Organic Search Performance'].empty:
        reports['organic_traffic'] = (
            seo_data['Organic Search Performance']
            .groupby(['firstUserSource', 'firstUserMedium'])
            .agg({
                'sessions': 'sum',
                'engagementRate': 'mean'
            })
            .sort_values('sessions', ascending=False)
        )
    
    return reports

def refresh_data():
    """Always refresh data from Feb 10, 2025 to today"""
    fixed_start_date = "2025-02-10"
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    sheets_service, analytics_client = initialize_services()
    if not sheets_service or not analytics_client:
        return False
    
    success_count = 0
    for source in SEO_DATA_SOURCES:
        data = fetch_analytics_data(
            client=analytics_client,
            dimensions=source["dimensions"],
            metrics=source["metrics"],
            date_ranges=[(fixed_start_date, end_date)],
            filter_expression=source.get("filter")
        )
        if data is not None:
            if save_data(data, source["filename"], sheets_service):
                success_count += 1
    return success_count > 0

# Add this to your data_extractor.py file

def calculate_ltv_metrics(analytics_client):
    """Calculate LTV metrics from GA4 data"""
    try:
        # Get user acquisition data
        acquisition_data = fetch_analytics_data(
            client=analytics_client,
            dimensions=["date", "firstUserSource", "firstUserMedium", "userId"],
            metrics=["userEngagementDuration", "purchaseRevenue"],
            date_ranges=[("2025-02-10", "today")]  # Your fixed start date
        )
        
        # Get user retention data
        retention_data = fetch_analytics_data(
            client=analytics_client,
            dimensions=["date", "userId"],
            metrics=["sessions", "purchaseRevenue"],
            date_ranges=[("2025-02-10", "today")]
        )
        
        if acquisition_data is None or retention_data is None:
            return None
            
        # Merge and calculate LTV metrics
        ltv_data = pd.merge(
            acquisition_data,
            retention_data.groupby('userId').agg({
                'sessions': 'sum',
                'purchaseRevenue': 'sum'
            }).reset_index(),
            on='userId',
            how='left'
        )
        
        # Calculate metrics
        ltv_data['days_since_first_visit'] = (
            pd.to_datetime('today') - pd.to_datetime(ltv_data['date'])
        ).dt.days
        
        # Create LTV buckets based on revenue
        conditions = [
            (ltv_data['purchaseRevenue_sum'] >= 100),
            (ltv_data['purchaseRevenue_sum'] >= 50),
            (ltv_data['purchaseRevenue_sum'] > 0),
            (ltv_data['purchaseRevenue_sum'] == 0)
        ]
        choices = ['high', 'medium', 'low', 'none']
        ltv_data['ltv_bucket'] = np.select(conditions, choices, default='none')
        
        return ltv_data.rename(columns={
            'purchaseRevenue_sum': 'user_lifetime_revenue',
            'sessions_sum': 'user_lifetime_sessions',
            'firstUserSource': 'acquisition_source',
            'firstUserMedium': 'acquisition_medium'
        })
        
    except Exception as e:
        print(f"Error calculating LTV metrics: {e}")
        return None

# Add to SEO_DATA_SOURCES list in data_extractor.py
ADDITIONAL_DATA_SOURCES = [
    # Audience/Segments
    {
        "name": "Audience Segments",
        "filename": "audience_segments.csv",
        "dimensions": ["date", "audienceName", "audienceType"],
        "metrics": ["activeUsers", "newUsers", "conversions", "purchaseRevenue"]
    },
    
    # E-commerce
    {
        "name": "E-commerce",
        "filename": "ecommerce.csv",
        "dimensions": ["date", "productName", "productCategory"],
        "metrics": ["itemsPurchased", "itemRevenue", "purchaseRevenue"]
    },
    
    # Funnel Analysis
    {
        "name": "Funnel Analysis",
        "filename": "funnel.csv",
        "dimensions": ["date", "funnelStep"],
        "metrics": ["funnelConversions", "funnelDropOffRate"]
    },
    
    # Retention
    {
        "name": "Retention",
        "filename": "retention.csv",
        "dimensions": ["date", "cohort"],
        "metrics": ["retainedUsers", "retentionRate"]
    },
    
    # Errors
    {
        "name": "Error Tracking",
        "filename": "errors.csv",
        "dimensions": ["date", "eventName", "pagePath"],
        "metrics": ["eventCount"],
        "filter": "eventName==error"
    }
]

#**************************************************************************
#SMM DataExtraction
# Add these functions to data_extractor.py
def load_social_media_data(file_path, platform):
    """Load social media data from CSV/Excel"""
    try:
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        else:
            data = pd.read_excel(file_path)
            
        # Standardize column names
        data.columns = data.columns.str.lower().str.replace(' ', '_')
        
        # Platform-specific processing
        if platform == 'facebook':
            data['date'] = pd.to_datetime(data['publish_time']).dt.date
        elif platform == 'instagram':
            data['date'] = pd.to_datetime(data['date']).dt.date
        elif platform == 'linkedin':
            data['date'] = pd.to_datetime(data['created_date']).dt.date
            
        return data
        
    except Exception as e:
        print(f"Error loading {platform} data: {e}")
        return pd.DataFrame()

def fetch_social_media_data(sheets_service):
    """Process all social media data"""
    platforms = {
        'facebook': 'FacebookData.csv',
        'instagram': 'InstagramData.csv',
        'linkedin': 'LinkedInData.xlsx',
        'youtube': 'YouTubeData.csv',
        'twitter': 'TwitterData.csv'
    }
    
    results = {}
    for platform, filename in platforms.items():
        data = load_social_media_data(os.path.join(OUTPUT_DIR, filename), platform)
        if not data.empty:
            sheet_name = f"{platform}_data"
            if save_data(data, f"{platform}.csv", sheets_service):
                results[platform] = data
                
    return results

# LinkedIn data extraction
def load_linkedin_excel_data(file_path):
    """Load LinkedIn data from Excel file"""
    try:
        # Read all sheets from the Excel file
        xls = pd.ExcelFile(file_path)
        
        # Load metrics sheet
        metrics_df = pd.read_excel(xls, sheet_name='Metrics')
        metrics_df['Date'] = pd.to_datetime(metrics_df['Date'])
        
        # Load posts sheet
        posts_df = pd.read_excel(xls, sheet_name='Posts')
        posts_df['Created date'] = pd.to_datetime(posts_df['Created date'])
        
        return metrics_df, posts_df
        
    except Exception as e:
        print(f"Error loading LinkedIn data: {e}")
        return pd.DataFrame(), pd.DataFrame()
#**************************************************************************

def ensure_worksheets_exist(sheets_service):
    """Ensure all required worksheets exist with headers"""
    required_sheets = {
        'app_data': ["date", "appVersion", "platform", "userEngagementDuration"],
        'funnel_data': ["date", "funnelStep", "funnelConversions"],
        'retention_data': ["date", "cohort", "retentionRate"],
        'error_data': ["date", "eventName", "eventCount"],
        'audience_data': ["audienceName", "activeUsers", "conversions"]
    }
    
    for sheet_name, headers in required_sheets.items():
        try:
            # Try to get the sheet
            sheet = sheets_service.spreadsheets().get(
                spreadsheetId=SPREADSHEET_ID,
                ranges=[f"{sheet_name}!A1:Z1"],
                fields="sheets(properties.title)"
            ).execute()
            
            # If sheet doesn't exist, create it
            if not any(s['properties']['title'] == sheet_name for s in sheet.get('sheets', [])):
                create_sheet_with_headers(sheets_service, sheet_name, headers)
                
        except Exception as e:
            print(f"Error checking {sheet_name} sheet: {e}")
            create_sheet_with_headers(sheets_service, sheet_name, headers)

def create_sheet_with_headers(sheets_service, sheet_name, headers):
    """Create a new sheet with headers"""
    try:
        # Create the sheet
        create_sheet(sheets_service, sheet_name)
        
        # Add headers
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1",
            valueInputOption='USER_ENTERED',
            body={'values': [headers]}
        ).execute()
        
        print(f"✅ Created new sheet: {sheet_name}")
    except Exception as e:
        print(f"❌ Failed to create {sheet_name} sheet: {e}")


def main():
    print("\n" + "="*50)
    print("🚀 Starting SEO Data Pipeline")
    print("="*50 + "\n")
    
    sheets_service, analytics_client = initialize_services()
    if not sheets_service or not analytics_client:
        return
    
    # Specific date range: Feb 10, 2025 to today
    fixed_start_date = "2025-02-10"  # Hardcoded start date
    end_date = datetime.now().strftime('%Y-%m-%d')  # Dynamic end date
    date_ranges = [(fixed_start_date, end_date)]
    
    # Combine all data sources
    ALL_DATA_SOURCES = SEO_DATA_SOURCES + ADDITIONAL_DATA_SOURCES

    # Process all data sources
    success_count = 0
    success_count = 0
    for source in ALL_DATA_SOURCES:
        data = fetch_analytics_data(
            client=analytics_client,
            dimensions=source["dimensions"],
            metrics=source["metrics"],
            date_ranges=date_ranges,
            filter_expression=source.get("filter")
        )
        if data is not None:
            if save_data(data, source["filename"], sheets_service):
                success_count += 1
    
    # Calculate LTV metrics
    ltv_data = calculate_ltv_metrics(analytics_client)
    if ltv_data is not None:
        save_data(ltv_data, "ltv_metrics.csv", sheets_service)
    
    # Generate and save SEO report
    try:
        seo_report = generate_seo_report(analytics_client, SEARCH_CONSOLE_SITE_URL)
        
        for report_name, report_data in seo_report.items():
            filename = f"seo_{report_name}.csv"
            if save_data(report_data, filename, sheets_service):
                success_count += 1
    except Exception as e:
        print(f"⚠️ SEO Report generation skipped: {e}")
    
    print("\n" + "="*50)
    print(f"✅ Pipeline completed! {success_count} datasets saved")
    print(f"📊 Open your spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()