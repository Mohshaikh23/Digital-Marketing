import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from Shared_Components.components import display_metric

def analyze_ltv_data(ltv_data):
    st.success("LTV data loaded successfully!")
    ltv_data.columns = ltv_data.columns.str.lower().str.replace(' ', '_')
    
    st.header("📊 Key Metrics")
    cols = st.columns(4)
    metrics = [
        ('Average LTV', 'user_lifetime_revenue', 'mean', '${:,.2f}'),
        ('Median LTV', 'user_lifetime_revenue', 'median', '${:,.2f}'),
        ('Paying Users', 'user_lifetime_revenue', lambda x: (x > 0).mean() * 100, '{:.1f}%'),
        ('Avg Transactions', 'user_lifetime_transactions', 'mean', '{:.1f}')
    ]
    
    for col, (label, col_name, agg_func, fmt) in zip(cols, metrics):
        if col_name in ltv_data.columns:
            value = ltv_data[col_name].agg(agg_func)
            col.metric(label, fmt.format(value))
    
    st.header("📈 Distribution Analysis")
    if 'user_lifetime_revenue' in ltv_data.columns:
        fig = px.histogram(ltv_data, x='user_lifetime_revenue', nbins=50,
                          title='LTV Value Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    if 'date' in ltv_data.columns:
        st.header("🕰️ Cohort Analysis")
        ltv_data['cohort'] = pd.to_datetime(ltv_data['date']).dt.to_period('M')
        cohort_data = ltv_data.groupby('cohort').agg({
            'user_lifetime_revenue': ['mean', 'median', 'count'],
            'user_id': 'nunique'
        }).reset_index()
        
        cohort_data.columns = ['_'.join(col).strip() if col[1] else col[0] 
                             for col in cohort_data.columns.values]
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(cohort_data, x='cohort', y='user_lifetime_revenue_mean',
                         title='Average LTV by Cohort')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(cohort_data, x='cohort', y='user_id_nunique',
                        title='Users by Cohort')
            st.plotly_chart(fig, use_container_width=True)
    
    if all(col in ltv_data.columns for col in ['acquisition_source', 'user_lifetime_revenue']):
        st.header("📡 Acquisition Performance")
        source_data = ltv_data.groupby('acquisition_source').agg({
            'user_lifetime_revenue': ['mean', 'count'],
            'user_lifetime_transactions': 'mean'
        }).reset_index()
        
        source_data.columns = ['source', 'avg_ltv', 'users', 'avg_transactions']
        
        tab1, tab2 = st.tabs(["By LTV", "By Volume"])
        with tab1:
            fig = px.bar(source_data.sort_values('avg_ltv', ascending=False),
                        x='source', y='avg_ltv',
                        title='Average LTV by Acquisition Source')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.pie(source_data, values='users', names='source',
                        title='User Acquisition Distribution')
            st.plotly_chart(fig, use_container_width=True)

def page_ltv(ltv_data=None):
    st.title("💰 Customer Lifetime Value Analysis")
    
    if ltv_data is not None and not ltv_data.empty:
        return analyze_ltv_data(ltv_data)
    
    st.warning("No direct LTV data available. Attempting to derive from available data...")
    st.error("""
    Unable to calculate LTV. You need one of these data sources:
    
    1. **Direct LTV Data** (preferred):
       - Worksheet named "LTV" with columns:
         - `user_id`, `user_lifetime_revenue`, `user_lifetime_transactions`, `date`
    
    2. **Derived from Analytics**:
       - Acquisition data (userId, firstUserSource, date)
       - Conversion data (userId, purchaseRevenue, transactions)
    """)
    
    if st.checkbox("Show sample LTV analysis for demonstration"):
        st.info("Displaying sample data for demonstration purposes")
        sample_size = 1000
        np.random.seed(42)
        
        sample_ltv = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(sample_size)],
            'user_lifetime_revenue': np.random.lognormal(3, 1, sample_size).round(2),
            'user_lifetime_transactions': np.random.poisson(3, sample_size),
            'date': pd.date_range('2025-02-10', periods=sample_size).strftime('%Y-%m-%d'),
            'acquisition_source': np.random.choice(['google', 'facebook', 'direct', 'organic'], sample_size),
            'acquisition_medium': np.random.choice(['cpc', 'organic', 'referral', 'email'], sample_size)
        })
        
        conditions = [
            (sample_ltv['user_lifetime_revenue'] > 100),
            (sample_ltv['user_lifetime_revenue'] > 50),
            (sample_ltv['user_lifetime_revenue'] > 0),
            (sample_ltv['user_lifetime_revenue'] == 0)
        ]
        choices = ['high', 'medium', 'low', 'none']
        sample_ltv['ltv_bucket'] = np.select(conditions, choices, default='none')
        
        analyze_ltv_data(sample_ltv)