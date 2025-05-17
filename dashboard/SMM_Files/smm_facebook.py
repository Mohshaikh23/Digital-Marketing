import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Shared_Components.components import display_metric
from datetime import datetime, timedelta

def page_facebook(facebook_data):
    st.title("📘 Facebook Metrics")
    st.markdown("Comprehensive analytics for Facebook performance")
    
    # Data validation
    if facebook_data is None or facebook_data.empty:
        st.warning("No Facebook data available")
        return
    
    # Convert date columns
    date_cols = [col for col in facebook_data.columns if 'date' in col.lower() or 'time' in col.lower()]
    for col in date_cols:
        facebook_data[col] = pd.to_datetime(facebook_data[col], errors='coerce')
    
    # Calculate engagement rate if not present
    if 'Engagement rate' not in facebook_data.columns and 'Reach' in facebook_data.columns and 'Reactions, comments and shares' in facebook_data.columns:
        facebook_data['Engagement rate'] = (facebook_data['Reactions, comments and shares'] / facebook_data['Reach']) * 100
    
    # Main metrics
    st.header("📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_posts = len(facebook_data)
        display_metric("Total Posts", total_posts, 0)
    with col2:
        total_reach = facebook_data["Reach"].sum()
        display_metric("Total Reach", f"{total_reach:,}", 0)
    with col3:
        total_engagement = facebook_data["Reactions, comments and shares"].sum()
        display_metric("Total Engagement", f"{total_engagement:,}", 0)
    with col4:
        avg_engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0
        display_metric("Avg Engagement Rate", f"{avg_engagement_rate:.2f}%", 0)
    
    # Engagement breakdown
    st.header("🧩 Engagement Breakdown")
    if all(col in facebook_data.columns for col in ["Reactions", "Comments", "Shares"]):
        engagement_cols = st.columns(3)
        with engagement_cols[0]:
            total_reactions = facebook_data["Reactions"].sum()
            display_metric("Total Reactions", f"{total_reactions:,}", 0)
        with engagement_cols[1]:
            total_comments = facebook_data["Comments"].sum()
            display_metric("Total Comments", f"{total_comments:,}", 0)
        with engagement_cols[2]:
            total_shares = facebook_data["Shares"].sum()
            display_metric("Total Shares", f"{total_shares:,}", 0)
        
        # Engagement composition
        engagement_data = pd.DataFrame({
            "Type": ["Reactions", "Comments", "Shares"],
            "Count": [total_reactions, total_comments, total_shares]
        })
        fig = px.pie(engagement_data, values="Count", names="Type", 
                     title="Engagement Composition")
        st.plotly_chart(fig, use_container_width=True)
    
    # Time series analysis
    st.header("⏳ Performance Over Time")
    time_group = st.selectbox("Group by", ["Day", "Week", "Month"], index=1)
    
    if time_group == "Day":
        time_period = "D"
    elif time_group == "Week":
        time_period = "W"
    else:
        time_period = "M"
    
    time_series = facebook_data.set_index('Publish time').resample(time_period).agg({
        'Reach': 'sum',
        'Reactions, comments and shares': 'sum',
        'Views': 'sum',
        'Total clicks': 'sum'
    }).reset_index()
    
    fig = px.line(time_series, x="Publish time", 
                 y=["Reach", "Reactions, comments and shares", "Views", "Total clicks"],
                 title=f"{time_group}ly Performance Trends")
    st.plotly_chart(fig, use_container_width=True)
    
    # Content analysis
    st.header("📝 Content Analysis")
    
    # Post type analysis (with existence check)
    if "Post type" in facebook_data.columns:
        st.subheader("Post Type Performance")
        
        # Create aggregation dictionary based on available columns
        agg_dict = {
            "Reach": "mean",
            "Reactions, comments and shares": "mean"
        }
        
        # Add engagement rate if it exists or can be calculated
        if 'Engagement rate' in facebook_data.columns:
            agg_dict["Engagement rate"] = "mean"
        
        post_type_stats = facebook_data.groupby("Post type").agg(agg_dict).reset_index()
        
        fig = px.bar(post_type_stats, x="Post type", y="Reach",
                    title="Average Reach by Post Type")
        st.plotly_chart(fig, use_container_width=True)
        
        if 'Engagement rate' in post_type_stats.columns:
            fig = px.bar(post_type_stats, x="Post type", y="Engagement rate",
                        title="Average Engagement Rate by Post Type")
            st.plotly_chart(fig, use_container_width=True)
    
    # Video content analysis (with existence checks)
    if "Duration (secs)" in facebook_data.columns and facebook_data["Duration (secs)"].notna().any():
        st.subheader("Video Performance")
        
        # Duration vs Engagement
        fig = px.scatter(facebook_data, x="Duration (secs)", y="Reactions, comments and shares",
                        color="Reach", size="Views",
                        title="Video Duration vs Engagement")
        st.plotly_chart(fig, use_container_width=True)
        
        # Watch time analysis (with existence check)
        if "Seconds viewed" in facebook_data.columns and "Duration (secs)" in facebook_data.columns:
            facebook_data["Completion rate"] = (facebook_data["Seconds viewed"] / 
                                             facebook_data["Duration (secs)"]) * 100
            fig = px.histogram(facebook_data, x="Completion rate",
                              title="Video Completion Rates")
            st.plotly_chart(fig, use_container_width=True)
    
    # Monetization analysis (with existence checks)
    if "Estimated earnings (USD)" in facebook_data.columns:
        st.header("💰 Monetization Metrics")
        
        monetization_cols = st.columns(3)
        with monetization_cols[0]:
            total_earnings = facebook_data["Estimated earnings (USD)"].sum()
            display_metric("Total Earnings", f"${total_earnings:,.2f}", 0)
        with monetization_cols[1]:
            if "Ad CPM (USD)" in facebook_data.columns:
                avg_cpm = facebook_data["Ad CPM (USD)"].mean()
                display_metric("Avg CPM", f"${avg_cpm:.2f}", 0)
        with monetization_cols[2]:
            if "Ad impressions" in facebook_data.columns:
                total_impressions = facebook_data["Ad impressions"].sum()
                display_metric("Ad Impressions", f"{total_impressions:,}", 0)
        
        # Earnings trend
        if "Estimated earnings (USD)" in facebook_data.columns:
            earnings_trend = facebook_data.set_index('Publish time').resample(time_period)["Estimated earnings (USD)"].sum().reset_index()
            fig = px.line(earnings_trend, x="Publish time", y="Estimated earnings (USD)",
                         title=f"{time_group}ly Earnings Trend")
            st.plotly_chart(fig, use_container_width=True)
    
    # Top performing content
    st.header("🏆 Top Performing Content")
    
    top_cols = st.columns(2)
    with top_cols[0]:
        st.subheader("By Engagement")
        top_engagement = facebook_data.nlargest(5, "Reactions, comments and shares")[
            ["Title", "Publish time", "Reach", "Reactions, comments and shares", "Post type"]
        ]
        st.dataframe(top_engagement)
    
    with top_cols[1]:
        st.subheader("By Reach")
        top_reach = facebook_data.nlargest(5, "Reach")[
            ["Title", "Publish time", "Reach", "Reactions, comments and shares", "Post type"]
        ]
        st.dataframe(top_reach)
