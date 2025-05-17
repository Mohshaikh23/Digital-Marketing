WORKSHEET_MAPPING = {
    # SEO/GA4 Data
    "user_traffic": {
        "primary": "user_traffic",
        "alternatives": [],
        "required_cols": ["date", "totalUsers", "activeUsers", "sessions", "bounceRate"]
    },
    "engagement": {
        "primary": "engagement", 
        "alternatives": [],
        "required_cols": ["date", "averageSessionDuration", "screenPageViewsPerSession", "eventCount"]
    },
    "acquisition": {
        "primary": "acquisition",
        "alternatives": [],
        "required_cols": ["date", "sessionSource", "sessionMedium", "sessions", "totalUsers"]
    },
    "page_views": {
        "primary": "page_views",
        "alternatives": [],
        "required_cols": ["date", "pageTitle", "screenPageViews", "screenPageViewsPerSession"]
    },
    "demographics": {
        "primary": "demographics",
        "alternatives": [],
        "required_cols": ["date", "country", "activeUsers","userAgeBracket", "userGender"]
    },
    "device": {
        "primary": "technology",
        "alternatives": [],
        "required_cols": ["date", "deviceCategory", "operatingSystem", "browser"]
    },
    "events": {
        "primary": "events",
        "alternatives": [],
        "required_cols": ["date", "eventName", "eventCount"]
    },
    "site_speed": {
        "primary": "site_speed",
        "alternatives": [],
        "required_cols": ["date", "pagePath", "averageSessionDuration"]
    },
    "audience": {
        "primary": "audience",
        "alternatives": ["audience_segments", "user_segments"],
        "required_cols": ["audienceName", "activeUsers", "conversions"]
    },
    
    # SEO Data
    "search_console": {
        "primary": "seo_top_queries",
        "alternatives": [],
        "required_cols": ["clicks", "impressions", "position", "ctr"]
    },
    "seo_pages": {
        "primary": "seo_top_pages",
        "alternatives": [],
        "required_cols": ["clicks", "impressions", "position"]
    },
    "seo_content": {
        "primary": "seo_content_engagement",
        "alternatives": [],
        "required_cols": ["screenPageViews", "engagementRate"]
    },
    "organic_search": {
        "primary": "organic_search",
        "alternatives": [],
        "required_cols": ["date", "firstUserSource", "firstUserMedium", "sessions"]
    },
    "landing_pages": {
        "primary": "seo_landing_pages",
        "alternatives": [],
        "required_cols": ["date", "landingPage", "sessionSource", "sessions"]
    }
}

SMM_COLUMN_MAPPING = {
    "facebook": {
        "date": ["Publish time", "Date"],
        "title": ["Title", "Post title"],
        "reach": ["Reach", "Total reach"],
        "engagement": ["Reactions, comments and shares", "Engagement"]
    },
    "instagram": {
        "date": ["Date"],
        "title": ["Title", "Caption"],
        "reach": ["Reach"],
        "engagement": ["Likes", "Engagement"]
    },
    "linkedin": {
        "date": ["Created date", "Date"],
        "title": ["Post title", "Title"],
        "reach": ["Impressions", "Total impressions"],
        "engagement": ["Engagement rate", "Engagement"]
    },
    "youtube": {
        "date": ["Date"],
        "title": ["Title"],
        "views": ["Views"],
        "watch_time": ["Watch time (minutes)"]
    },
    "x": {
        "date": ["Date"],
        "title": ["Tweet text"],
        "impressions": ["Impressions"],
        "engagement": ["Engagements"]
    }
}
