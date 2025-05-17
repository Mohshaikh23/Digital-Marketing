from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from config import GA4_PROPERTY_ID, GA4_VALID_DIMENSIONS, GA4_VALID_METRICS, METRIC_ALIASES
import pandas as pd
from datetime import datetime

def translate_metrics(metrics):
    """Convert deprecated metrics to current GA4 equivalents"""
    return [METRIC_ALIASES.get(m, m) for m in metrics]

def validate_ga4_fields(dimensions, metrics):
    """Enhanced validation with helpful error messages"""
    invalid_dims = [d for d in dimensions if d not in GA4_VALID_DIMENSIONS]
    invalid_mets = [m for m in metrics if m not in GA4_VALID_METRICS]
    
    if invalid_dims or invalid_mets:
        suggestion_map = {
            'userAgeBracket': 'age',
            'userGender': 'gender',
            'totalRevenue': 'purchaseRevenue',
            'browser': 'deviceCategory',
            'operatingSystem': 'deviceCategory'
        }
        
        suggestions = []
        for field in invalid_dims + invalid_mets:
            if field in suggestion_map:
                suggestions.append(f"'{field}' should be replaced with '{suggestion_map[field]}'")
        
        error_msg = (
            f"Invalid GA4 fields:\n"
            f"Dimensions: {invalid_dims}\n"
            f"Metrics: {invalid_mets}\n"
        )
        if suggestions:
            error_msg += "Suggestions:\n" + "\n".join(suggestions) + "\n"
        error_msg += "See valid fields at: https://ga-dev-tools.web.app/ga4/dimensions-metrics-explorer/"
        
        raise ValueError(error_msg)

def fetch_analytics_data(client, dimensions, metrics, date_ranges, filter_expression=None):
    """Safe GA4 data fetcher with validation and post-processing"""
    try:
        # Translate and validate metrics
        translated_metrics = translate_metrics(metrics)
        validate_ga4_fields(dimensions, translated_metrics)
        
        # Prepare and execute request
        request = RunReportRequest(
            property=GA4_PROPERTY_ID,
            dimensions=[Dimension(name=dim) for dim in dimensions],
            metrics=[Metric(name=m) for m in translated_metrics],
            date_ranges=[DateRange(start_date=start, end_date=end) 
                        for start, end in date_ranges]
        )
        
        if filter_expression:
            # Add filter handling here
            pass
            
        response = client.run_report(request)
        
        if not response.rows:
            print("⚠️ No data returned from Analytics API")
            return None
            
        # Process response into DataFrame
        df = process_ga4_response(response, dimensions, metrics, translated_metrics)
        
        # Calculate derived metrics
        if 'bounceRate' in metrics:
            df['bounceRate'] = 1 - (df['engagedSessions']/df['sessions'])
        if 'engagementRate' in metrics:
            df['engagementRate'] = df['engagedSessions']/df['sessions']
            
        return df
        
    except Exception as e:
        print(f"❌ GA4 API Error: {str(e)}")
        return None

def process_ga4_response(response, dimensions, orig_metrics, translated_metrics):
    """Convert GA4 API response to DataFrame"""
    rows = []
    for row in response.rows:
        row_data = {}
        for i, dim in enumerate(dimensions):
            val = row.dimension_values[i].value
            row_data[dim] = datetime.strptime(val, "%Y%m%d").strftime("%Y-%m-%d") if dim == "date" else val
                
        for i, (orig_met, trans_met) in enumerate(zip(orig_metrics, translated_metrics)):
            try:
                row_data[orig_met] = float(row.metric_values[i].value)
            except:
                row_data[orig_met] = row.metric_values[i].value
                
        rows.append(row_data)
        
    return pd.DataFrame(rows)[dimensions + orig_metrics]