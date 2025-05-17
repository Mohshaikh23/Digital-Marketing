from datetime import datetime
import logging
import sys
import os
import pandas as pd
from typing import Dict, Any

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
pd.set_option('future.no_silent_downcasting', True)

# Import from other modules
from google_services import initialize_services
from analytics_extractor import fetch_analytics_data
from google_sheets import save_data
from seo_reports import generate_seo_report
from ltv_calculator import calculate_ltv_metrics
from social_media import fetch_social_media_data
from data_utils import clean_data_for_sheets
from config import (
    SPREADSHEET_ID,
    FIXED_START_DATE,
    SEO_DATA_SOURCES,
    ADDITIONAL_DATA_SOURCES,
    SEARCH_CONSOLE_SITE_URL,
    OUTPUT_DIR,
    SERVICE_ACCOUNT_FILE
)

print(f"Service account should be at: {os.path.abspath(SERVICE_ACCOUNT_FILE)}")
print(f"File exists: {os.path.exists(SERVICE_ACCOUNT_FILE)}")

# Configure logging (Windows-compatible)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, 'seo_pipeline.log')), 
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_data_for_sheets(data: pd.DataFrame) -> pd.DataFrame:
    """Clean data to be Google Sheets compatible"""
    if data is None or data.empty:
        return data
        
    def clean_value(x):
        if pd.isna(x):
            return ""
        if isinstance(x, str):
            # Remove problematic characters and normalize
            cleaned = (x.replace('\n', ' ')
                      .replace('\r', '')
                      .replace('"', "'")
                      .strip())
            # Remove non-printable ASCII characters
            return ''.join(char for char in cleaned if 32 <= ord(char) <= 126)
        return x
        
    return data.map(clean_value)


def get_date_range():
    """Get fixed date range from Feb 10, 2025 to today"""
    return [
        (FIXED_START_DATE, datetime.now().strftime('%Y-%m-%d'))
    ]

def process_data_sources(analytics_client, sheets_service) -> int:
    """Process all GA4 data sources with enhanced error handling"""
    success_count = 0
    all_sources = SEO_DATA_SOURCES + ADDITIONAL_DATA_SOURCES
    
    for source in all_sources:
        try:
            logger.info(f"Processing {source['name']}...")
            
            # Skip known problematic sources (remove demographics from this list)
            if source['name'] in ['E-commerce']:  # Removed 'User Demographics' from skip list
                logger.warning(f"Skipping {source['name']} - known compatibility issues")
                continue
                
            data = fetch_analytics_data(
                client=analytics_client,
                dimensions=source.get("dimensions", []),
                metrics=source.get("metrics", []),
                date_ranges=get_date_range(),
                filter_expression=source.get("filter")
            )
            
            if data is not None and not data.empty:
                data = clean_data_for_sheets(data)
                
                if save_data(data, source["filename"], sheets_service):
                    success_count += 1
                    logger.info(f"SUCCESS - Saved {source['name']}")
                else:
                    logger.warning(f"WARNING - Failed to save {source['name']}")
            else:
                logger.warning(f"WARNING - No data returned for {source['name']}")
                
        except Exception as e:
            logger.error(f"ERROR - Processing {source.get('name', 'unknown')}: {str(e)}")
    
    return success_count

def generate_reports(analytics_client, sheets_service) -> int:
    """Generate and save SEO reports with enhanced error handling"""
    report_count = 0
    try:
        logger.info("Generating SEO reports...")
        seo_report = generate_seo_report(analytics_client, SEARCH_CONSOLE_SITE_URL)
        
        if seo_report:
            for report_name, report_data in seo_report.items():
                try:
                    report_data = clean_data_for_sheets(report_data)
                    filename = f"seo_{report_name}.csv"
                    
                    # Additional cleaning for content performance data
                    if report_name == 'content_performance':
                        # Extra cleaning for problematic content
                        report_data = report_data.applymap(lambda x: 
                            x.encode('ascii', 'ignore').decode('ascii') if isinstance(x, str) else x)
                        report_data = report_data.fillna('')
                    
                    if save_data(report_data, filename, sheets_service):
                        report_count += 1
                        logger.info(f"SUCCESS - Saved report: {filename}")
                    else:
                        logger.warning(f"WARNING - Failed to save report: {filename}")
                except Exception as e:
                    logger.error(f"ERROR - Processing report {report_name}: {str(e)}")
    except Exception as e:
        logger.error(f"ERROR - Report generation failed: {str(e)}")
    
    return report_count

def print_summary(metrics: Dict[str, Any]):
    """Print final summary in a Windows-compatible way"""
    border = "=" * 50
    summary = f"""
{border}
SEO Pipeline Execution Summary
{border}
- Processed {metrics['data_sources']} data sources
- Generated {metrics['reports']} reports
- LTV Metrics: {'SUCCESS' if metrics['ltv_calculated'] else 'FAILED'}
- Social Media: {metrics['social_media']} platforms processed
{border}
View your spreadsheet: 
https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
{border}
"""
    print(summary)

def validate_environment():
    """Check required files and configurations exist"""
    errors = []
    
    # Check analytics data directory exists
    if not os.path.exists('analytics_data'):
        errors.append("analytics_data directory not found")
    
    # Check Google credentials
    if not os.path.exists('credentials.json'):
        errors.append("Google credentials file not found")
    
    if errors:
        logger.error("Environment validation failed:")
        for error in errors:
            logger.error(f"- {error}")
        return False
    return True

def main():
    if not validate_environment():
        return
    
    """Main execution function"""
    print("\n" + "=" * 50)
    print("Starting SEO Data Pipeline".center(50))
    print("=" * 50 + "\n")
    
    # Initialize services
    sheets_service, analytics_client = initialize_services()
    if not sheets_service or not analytics_client:
        logger.error("Failed to initialize Google services")
        return
    
    # Track metrics
    metrics = {
        'data_sources': 0,
        'reports': 0,
        'ltv_calculated': False,
        'social_media': 0
    }
    
    try:
        # Process data sources
        metrics['data_sources'] = process_data_sources(analytics_client, sheets_service)
        
        # Generate reports
        metrics['reports'] = generate_reports(analytics_client, sheets_service)
        
        # Calculate LTV metrics
        try:
            ltv_data = calculate_ltv_metrics(analytics_client)
            if ltv_data is not None:
                ltv_data = clean_data_for_sheets(ltv_data)
                if save_data(ltv_data, "ltv_metrics.csv", sheets_service):
                    metrics['ltv_calculated'] = True
        except Exception as e:
            logger.error(f"LTV calculation failed: {str(e)}")
        
        # Process social media
        try:
            sm_data = fetch_social_media_data(sheets_service)
            metrics['social_media'] = len(sm_data) if sm_data else 0
        except Exception as e:
            logger.warning(f"Social media processing skipped: {str(e)}")
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
    finally:
        print_summary(metrics)

if __name__ == "__main__":
    main()