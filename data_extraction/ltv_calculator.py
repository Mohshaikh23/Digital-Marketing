import pandas as pd
import numpy as np
from datetime import datetime
from analytics_extractor import fetch_analytics_data

def calculate_ltv_metrics(analytics_client):
    try:
        # Get acquisition data
        acquisition_data = fetch_analytics_data(
            client=analytics_client,
            dimensions=["date", "firstUserSource", "firstUserMedium"],
            metrics=["userEngagementDuration", "purchaseRevenue"],
            date_ranges=[("2025-02-10", "today")]
        )
        
        # Get engagement data
        engagement_data = fetch_analytics_data(
            client=analytics_client,
            dimensions=["date", "firstUserSource"],
            metrics=["sessions", "purchaseRevenue"],
            date_ranges=[("2025-02-10", "today")]
        )
        
        if acquisition_data is None or engagement_data is None:
            return None
            
        # Aggregate engagement data with clear column names
        engagement_agg = engagement_data.groupby('firstUserSource').agg({
            'sessions': 'sum',
            'purchaseRevenue': 'sum'
        }).rename(columns={
            'sessions': 'total_sessions',
            'purchaseRevenue': 'total_revenue'
        }).reset_index()
        
        # Merge data
        ltv_data = pd.merge(
            acquisition_data,
            engagement_agg,
            on='firstUserSource',
            how='left'
        )
        
        # Calculate metrics
        ltv_data['days_since_first_visit'] = (
            pd.to_datetime('today') - pd.to_datetime(ltv_data['date'])
        ).dt.days
        
        # Create LTV buckets
        conditions = [
            (ltv_data['total_revenue'] >= 100),
            (ltv_data['total_revenue'] >= 50),
            (ltv_data['total_revenue'] > 0),
            (ltv_data['total_revenue'] == 0)
        ]
        choices = ['high', 'medium', 'low', 'none']
        ltv_data['ltv_bucket'] = np.select(conditions, choices, default='none')
        
        return ltv_data.rename(columns={
            'total_revenue': 'user_lifetime_revenue',
            'total_sessions': 'user_lifetime_sessions',
            'firstUserSource': 'acquisition_source',
            'firstUserMedium': 'acquisition_medium'
        })
        
    except Exception as e:
        print(f"Error calculating LTV metrics: {e}")
        return None
