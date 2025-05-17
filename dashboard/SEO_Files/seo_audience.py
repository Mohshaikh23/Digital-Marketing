import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from Shared_Components.components import display_metric

def page_audience(audience_data):
    st.title("👥 Audience & Segments Analysis")
    
    # Data validation and cleaning
    if audience_data is None or audience_data.empty:
        st.warning("No audience data available. Please check your data source.")
        return
    
    # Convert column names to lowercase for consistency
    audience_data.columns = audience_data.columns.str.lower()
    
    # Rename columns to match expected format
    column_mapping = {
        'audiencename': 'audienceName',
        'activeusers': 'activeUsers',
        'conversions': 'conversions',
        'purchaserevenue': 'purchaseRevenue',
        'date': 'date'
    }
    audience_data = audience_data.rename(columns=column_mapping)
    
    # Convert date column if exists
    if 'date' in audience_data.columns:
        try:
            audience_data['date'] = pd.to_datetime(audience_data['date'])
        except Exception as e:
            st.error(f"Error parsing date column: {str(e)}")
    
    # Check for required columns
    required_cols = ['audienceName', 'activeUsers']
    missing_cols = [col for col in required_cols if col not in audience_data.columns]
    
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        st.info("The following columns are available in your data:")
        st.write(list(audience_data.columns))
        return
    
    # Main metrics section
    st.header("Key Audience Metrics")
    
    col1, col2 = st.columns(2)  # Removed the third column since we don't have newUsers
    with col1:
        total_audiences = audience_data['audienceName'].nunique()
        display_metric("Total Audience Segments", total_audiences, 0)
    
    with col2:
        total_active = audience_data['activeUsers'].sum()
        prev_active = total_active * 0.95  # Simulating 5% growth for demo
        delta = ((total_active - prev_active) / prev_active) * 100
        display_metric("Total Active Users", f"{total_active:,}", delta)
    
    # Date filtering with safe defaults
    if 'date' in audience_data.columns:
        st.subheader("Date Range Filter")
        min_date = audience_data['date'].min().date()
        max_date = audience_data['date'].max().date()
        
        # Calculate safe default start date
        default_start = max(min_date, max_date - timedelta(days=30))
        
    # Audience composition analysis
    st.header("Audience Composition")
    
    # Top audiences by active users
    st.subheader("Top Performing Audiences")
    top_audiences = audience_data.groupby('audienceName')['activeUsers'].sum().nlargest(10).reset_index()
    
    fig = px.bar(
        top_audiences,
        x='activeUsers',
        y='audienceName',
        orientation='h',
        color='activeUsers',
        color_continuous_scale='tealrose',
        title='Top 10 Audiences by Active Users'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Conversion analysis if available
    if 'conversions' in audience_data.columns:
        st.subheader("Conversion Performance")
        
        # Calculate conversion metrics
        conversion_data = audience_data.groupby('audienceName').agg({
            'activeUsers': 'sum',
            'conversions': 'sum'
        }).reset_index()
        conversion_data['conversion_rate'] = (conversion_data['conversions'] / conversion_data['activeUsers']) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            # Conversion rate chart
            fig = px.bar(
                conversion_data.sort_values('conversion_rate', ascending=False).head(10),
                x='audienceName',
                y='conversion_rate',
                title='Top Conversion Rates by Audience',
                labels={'conversion_rate': 'Conversion Rate (%)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Conversion volume chart
            fig = px.pie(
                conversion_data.nlargest(5, 'conversions'),
                values='conversions',
                names='audienceName',
                title='Conversion Distribution (Top 5)'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Time series trends if date available
    if 'date' in audience_data.columns:
        st.header("Temporal Trends")
        
        # Select audiences to display
        top_audiences_list = audience_data.groupby('audienceName')['activeUsers'].sum().nlargest(3).index.tolist()
        filtered_data = audience_data[audience_data['audienceName'].isin(top_audiences_list)]
        
        # Create time series chart
        fig = px.line(
            filtered_data.groupby(['date', 'audienceName'])['activeUsers'].sum().reset_index(),
            x='date',
            y='activeUsers',
            color='audienceName',
            title='Active Users Trend for Top 3 Audiences',
            labels={'activeUsers': 'Active Users', 'date': 'Date'}
        )
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # Raw data preview
    st.subheader("Data Preview")
    st.dataframe(audience_data, height=300)
    