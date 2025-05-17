from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from config import GA4_PROPERTY_ID
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def fetch_demographics_data(analytics_client, start_date="2025-02-10", end_date=None):
    """Fetch valid demographics data from GA4"""
    try:
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        request = RunReportRequest(
            property=GA4_PROPERTY_ID,
            dimensions=[
                Dimension(name="date"),
                Dimension(name="country"),
                Dimension(name="city"),
                Dimension(name="region"), 
                Dimension(name="language")
            ],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="engagedSessions")
            ],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)]
        )
        
        response = analytics_client.run_report(request)
        
        if not response.rows:
            logger.warning("No demographics data returned from GA4")
            return pd.DataFrame()
            
        # Process response
        rows = []
        for row in response.rows:
            rows.append({
                "date": row.dimension_values[0].value,
                "country": row.dimension_values[1].value,
                "city": row.dimension_values[2].value,
                "region": row.dimension_values[3].value,
                "language": row.dimension_values[4].value,
                "users": int(row.metric_values[0].value),
                "engagedSessions": int(row.metric_values[1].value)
            })
            
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        df['engagementRate'] = df['engagedSessions'] / df['users']
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching demographics: {str(e)}")
        return pd.DataFrame()