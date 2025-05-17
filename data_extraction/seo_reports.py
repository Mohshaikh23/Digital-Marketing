import pandas as pd
from analytics_extractor import fetch_analytics_data
from search_console import fetch_search_console_data
from config import SEARCH_CONSOLE_SITE_URL
from config import SEO_DATA_SOURCES, SEARCH_CONSOLE_SITE_URL

def generate_seo_report(analytics_client, search_console_site_url):
    """Generate reports using valid GA4 fields"""
    print("\n🔍 Generating Comprehensive SEO Report...")
    
    try:
        # 1. Get Search Console Data
        sc_data = fetch_search_console_data(search_console_site_url)
        
        # 2. Get Analytics Data for SEO
        report_data = {
            'top_queries': None,
            'top_pages': None,
            'content_performance': None
        }
        
        if not sc_data.empty:
            report_data['top_queries'] = (sc_data.groupby('query')
                .agg({'clicks':'sum', 'impressions':'sum', 'position':'mean'})
                .sort_values('clicks', ascending=False)
                .head(50))
                
            report_data['top_pages'] = (sc_data.groupby('page')
                .agg({'clicks':'sum', 'impressions':'sum'})
                .sort_values('clicks', ascending=False)
                .head(50))
        
        # Get content performance from GA4
        content_data = fetch_analytics_data(
            client=analytics_client,
            dimensions=["pagePath", "pageTitle"],
            metrics=["screenPageViews", "engagedSessions"],
            date_ranges=[("30daysAgo", "today")]
        )
        
        if content_data is not None:
            content_data['engagementRate'] = content_data['engagedSessions'] / content_data['screenPageViews']
            report_data['content_performance'] = content_data.sort_values('screenPageViews', ascending=False)
        
        return {k: v for k, v in report_data.items() if v is not None}
        
    except Exception as e:
        print(f"❌ SEO Report Error: {e}")
        return None