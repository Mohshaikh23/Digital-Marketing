import os

# Google API Configuration
SPREADSHEET_ID = "17gv72J54TDcW9wSAtG0cKGXty0zxfgeKZVLEp65bYcc"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "..", "service_account.json")

# Verify the path exists
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    print(f"⚠️ Warning: Service account file not found at: {SERVICE_ACCOUNT_FILE}")

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/youtube.readonly'
]
OUTPUT_DIR = "analytics_data"
SEARCH_CONSOLE_SITE_URL = "https://proefficientdataentry.com/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# GA4 Property ID
GA4_PROPERTY_ID = "properties/477624929"

# Date Configuration
FIXED_START_DATE = "2025-02-10"  # Hardcoded start date for all data extraction

# Valid GA4 Dimensions and Metrics (Updated for GA4 API)
GA4_VALID_DIMENSIONS = [
    'date', 'country', 'deviceCategory', 'pagePath', 'pageTitle',
    'sessionSource', 'sessionMedium', 'eventName', 'landingPage',
    'firstUserSource', 'firstUserMedium', 'audienceName', 'itemName',
    'itemCategory', 'searchTerm', 'city', 'region', 'language',
    'platform', 'browser', 'trafficMedium', 'trafficSource',
]

GA4_VALID_METRICS = [
    'activeUsers', 'engagedSessions', 'eventCount', 'sessions',
    'userEngagementDuration', 'screenPageViews', 'conversions',
    'itemsPurchased', 'itemRevenue', 'purchaseRevenue',
    'totalRevenue', 'sessionsPerUser', 'eventsPerSession',
    'averageSessionDuration', 'engagementRate'
]

SEO_REPORT_CONFIG = {
    'top_queries_limit': 100,  # Add this line
    'top_pages_limit': 100,
    'content_engagement_limit': 100,
    'date_format': '%Y-%m-%d',
    'default_date_range': '90daysAgo',
    'min_sessions_threshold': 100
}

# Metrics Conversions (Map legacy names to GA4 valid metrics)
METRIC_ALIASES = {
    'totalUsers': 'activeUsers',
    'bounceRate': 'engagedSessions',  # Will be calculated as (1 - engagedSessions/sessions)
    'averageSessionDuration': 'userEngagementDuration',
    'screenPageViewsPerSession': 'screenPageViews',
    'engagementRate': '(engagedSessions/sessions)',
    'retentionRate': 'activeUsers',
    'newUsers': 'activeUsers',  # GA4 doesn't distinguish new vs returning in base metrics
    'pageviews': 'screenPageViews'
}

# SEO Data Sources Configuration (Updated for GA4 compatibility)
SEO_DATA_SOURCES = [
    # User Metrics
    {
        "name": "User Traffic",
        "filename": "user_traffic.csv",
        "dimensions": ["date"],
        "metrics": ["activeUsers", "engagedSessions", "sessions"]
    },
    
    # Engagement
    {
        "name": "User Engagement",
        "filename": "engagement.csv",
        "dimensions": ["date"],
        "metrics": ["userEngagementDuration", "screenPageViews", "eventCount"]
    },
    
    # Acquisition
    {
        "name": "Acquisition",
        "filename": "acquisition.csv",
        "dimensions": ["date", "sessionSource", "sessionMedium"],
        "metrics": ["sessions", "activeUsers", "engagedSessions"]
    },
    
    # Page Performance
    {
        "name": "Page Views",
        "filename": "page_views.csv",
        "dimensions": ["date", "pagePath", "pageTitle"],
        "metrics": ["screenPageViews"]
    },
    
    # Technology/Device
    {
        "name": "Technology",
        "filename": "technology.csv",
        "dimensions": ["date", "deviceCategory", "browser"],
        "metrics": ["activeUsers", "sessions"]
    },
    
    # SEO Landing Pages
    {
        "name": "SEO Landing Pages",
        "filename": "seo_landing_pages.csv",
        "dimensions": ["date", "landingPage", "sessionSource"],
        "metrics": ["sessions", "engagedSessions", "userEngagementDuration"]
    },
    
    # Content Engagement
    {
        "name": "Content Engagement",
        "filename": "content_engagement.csv",
        "dimensions": ["date", "pageTitle", "pagePath"],
        "metrics": ["screenPageViews", "activeUsers"]
    },
    
    # Organic Search Performance
    {
        "name": "Organic Search Performance",
        "filename": "organic_search.csv",
        "dimensions": ["date", "firstUserSource", "firstUserMedium"],
        "metrics": ["sessions", "activeUsers", "conversions"]
    },

    # User Demographics
    {
        "name": "User Demographics",
        "filename": "demographics.csv",
        "dimensions": ["date", "country", "city", "region", "language"],
        "metrics": ["activeUsers", "engagedSessions"],
        "skip": False
    },

    # SEO Top Queries
    {
        "name": "SEO Top Queries",
        "filename": "seo_top_queries.csv",
        "dimensions": ["date", "searchTerm", "pagePath"],
        "metrics": ["screenPageViews", "activeUsers"],
        "filter": "searchTerm!=(not provided);searchTerm!=(not set)",
        "order_by": "-screenPageViews",
        "limit": SEO_REPORT_CONFIG['top_queries_limit']
    },
]

# Additional Data Sources (GA4 compatible)
ADDITIONAL_DATA_SOURCES = [
    # Audience Segments
    {
        "name": "Audience Segments",
        "filename": "audience_segments.csv",
        "dimensions": ["date", "audienceName","sessions"],
        "metrics": ["activeUsers", "conversions", "purchaseRevenue","conversions"]
    },
    
    # E-commerce
    {
        "name": "E-commerce",
        "filename": "ecommerce.csv",
        "dimensions": ["date", "itemName", "itemCategory"],
        "metrics": ["itemsPurchased", "itemRevenue", "purchaseRevenue"]
    },
    
    # Events
    {
        "name": "Events",
        "filename": "events.csv",
        "dimensions": ["date", "eventName"],
        "metrics": ["eventCount"],
        "filter": "eventName==search"
    },
    
    # User Tracking
    {
        "name": "User Tracking",
        "filename": "user_tracking.csv",
        "dimensions": ["date", "firstUserSource", "firstUserMedium"],
        "metrics": ["activeUsers", "userEngagementDuration"]
    }
]

# Social Media Configuration
SOCIAL_MEDIA_PLATFORMS = {
    'facebook': {
        'filename': 'FacebookData.csv',
        'date_column': 'publish_time',
        'metrics': ['likes', 'shares', 'comments', 'reach']
    },
    'instagram': {
        'filename': 'InstagramData.csv',
        'date_column': 'date',
        'metrics': ['likes', 'comments', 'reach', 'saves']
    },
    'linkedin': {
        'filename': 'LinkedInData.xlsx',
        'date_column': 'created_date',
        'sheets': ['Metrics', 'Posts'],
        'metrics': ['impressions', 'clicks', 'shares']
    },
    'youtube': {
        'filename': 'YouTubeData.csv',
        'date_column': 'published_at',
        'metrics': ['views', 'likes', 'comments', 'watch_time']
    },
    'twitter': {
        'filename': 'TwitterData.csv',
        'date_column': 'created_at',
        'metrics': ['impressions', 'engagements', 'retweets']
    }
}

# Report Configuration
SEO_REPORT_CONFIG = {
    'top_queries_limit': 100,
    'top_pages_limit': 100,
    'content_engagement_limit': 100,
    'date_format': '%Y-%m-%d',
    'default_date_range': '90daysAgo',
    'min_sessions_threshold': 100  # Minimum sessions to be included in reports
}

# Calculated Metrics Configuration
CALCULATED_METRICS = {
    'bounceRate': {
        'formula': '1 - (engagedSessions/sessions)',
        'format': 'PERCENT'
    },
    'engagementRate': {
        'formula': 'engagedSessions/sessions',
        'format': 'PERCENT'
    },
    'avgTimeOnPage': {
        'formula': 'userEngagementDuration/screenPageViews',
        'format': 'TIME'
    }
}