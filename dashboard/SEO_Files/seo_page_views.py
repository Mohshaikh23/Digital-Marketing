import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from Shared_Components.components import display_metric

def page_page_views(page_views_data):
    st.title("📄 Page Views Analysis")
    st.markdown("""
        This page provides comprehensive insights into your website's page performance, 
        including traffic patterns, engagement metrics, and content effectiveness.
    """)

    if page_views_data is None or page_views_data.empty:
        st.warning("No page views data available.")
        return

    # Convert date column to datetime if it exists
    if "date" in page_views_data.columns:
        try:
            page_views_data["date"] = pd.to_datetime(page_views_data["date"])
        except Exception as e:
            st.error(f"Error converting date column: {e}")
            return

    available_cols = page_views_data.columns.tolist()
    
    # Check for required columns
    required_columns = {
        'pageTitle': 'Page Title',
        'screenPageViews': 'Page Views'
    }
    
    missing_columns = [col for col in required_columns if col not in available_cols]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        st.info("Available columns: " + ", ".join(available_cols))
        return

    st.header("🚀 Top Performing Pages")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_views = page_views_data["screenPageViews"].sum()
        display_metric("Total Page Views", f"{total_views:,}", 0)
    with col2:
        if "date" in available_cols:
            try:
                time_period = (page_views_data["date"].max() - page_views_data["date"].min()).days
                avg_views_per_day = total_views / time_period if time_period > 0 else 0
                display_metric("Avg Views/Day", f"{avg_views_per_day:,.1f}", 0)
            except Exception as e:
                display_metric("Avg Views/Day", "N/A", 0)
        else:
            display_metric("Avg Views/Day", "N/A", 0)
    with col3:
        unique_pages = page_views_data["pageTitle"].nunique()
        display_metric("Unique Pages", unique_pages, 0)

    # Create page stats with available metrics
    agg_functions = {
        "screenPageViews": ["sum", "mean", "std"]
    }
    
    # Add engagement metrics if available
    if "screenPageViewsPerSession" in available_cols:
        agg_functions["screenPageViewsPerSession"] = ["mean", "median"]
    
    page_stats = page_views_data.groupby("pageTitle").agg(agg_functions).reset_index()
    
    # Flatten multi-index columns
    page_stats.columns = ['_'.join(col).strip() if col[1] else col[0] for col in page_stats.columns.values]
    
    # Rename columns for better readability
    column_renames = {
        "screenPageViews_sum": "total_views",
        "screenPageViews_mean": "avg_daily_views",
        "screenPageViews_std": "views_std_dev"
    }
    
    if "screenPageViewsPerSession_mean" in page_stats.columns:
        column_renames["screenPageViewsPerSession_mean"] = "avg_views_per_session"
        column_renames["screenPageViewsPerSession_median"] = "median_views_per_session"
    
    page_stats = page_stats.rename(columns=column_renames)
    
    # Create tabs based on available data
    tab_names = ["By Total Views"]
    if "avg_views_per_session" in page_stats.columns:
        tab_names.append("By Engagement")
    tab_names.append("Raw Data")
    
    tabs = st.tabs(tab_names)
    
    with tabs[0]:  # By Total Views
        st.subheader("Top 10 Pages by Total Views")
        top_pages = page_stats.sort_values("total_views", ascending=False).head(10)
        fig = px.bar(top_pages, x="pageTitle", y="total_views", 
                     color="total_views", title="Top Pages by Total Views")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("View Consistency of Top Pages")
        fig = px.scatter(top_pages, x="avg_daily_views", y="views_std_dev",
                         size="total_views", hover_name="pageTitle",
                         title="Daily View Consistency (Size = Total Views)")
        st.plotly_chart(fig, use_container_width=True)
    
    if len(tabs) > 1 and "avg_views_per_session" in page_stats.columns:
        with tabs[1]:  # By Engagement
            st.subheader("Top 10 Pages by Engagement")
            engaged_pages = page_stats.sort_values("avg_views_per_session", ascending=False).head(10)
            fig = px.bar(engaged_pages, x="pageTitle", y="avg_views_per_session", 
                         color="avg_views_per_session", title="Top Pages by Views Per Session")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Views vs Engagement")
            fig = px.scatter(page_stats, x="total_views", y="avg_views_per_session",
                             hover_name="pageTitle", trendline="ols",
                             title="Total Views vs Views Per Session")
            st.plotly_chart(fig, use_container_width=True)
    
    with tabs[-1]:  # Raw Data
        st.subheader("All Page Metrics")
        st.dataframe(page_stats.sort_values("total_views", ascending=False))

    if "date" in available_cols:
        st.header("⏱ Time-Based Patterns")
        page_views_data["week"] = page_views_data["date"].dt.to_period("W").astype(str)
        weekly_views = page_views_data.groupby("week")["screenPageViews"].sum().reset_index()
        weekly_views["wow_growth"] = weekly_views["screenPageViews"].pct_change() * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekly Page View Trends")
            fig = px.line(weekly_views, x="week", y="screenPageViews", 
                          title="Total Page Views by Week")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Week-over-Week Growth")
            fig = px.bar(weekly_views, x="week", y="wow_growth", 
                          title="Weekly Growth Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        
        page_views_data["day_of_week"] = page_views_data["date"].dt.day_name()
        daily_pattern = page_views_data.groupby("day_of_week")["screenPageViews"].sum().reset_index()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_pattern["day_of_week"] = pd.Categorical(daily_pattern["day_of_week"], categories=day_order, ordered=True)
        daily_pattern = daily_pattern.sort_values("day_of_week")
        
        st.subheader("Page Views by Day of Week")
        fig = px.bar(daily_pattern, x="day_of_week", y="screenPageViews",
                     title="Page View Distribution by Weekday")
        st.plotly_chart(fig, use_container_width=True)