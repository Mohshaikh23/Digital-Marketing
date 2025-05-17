# In smm_linkedin.py - update the page_linkedin_analysis function
import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric
from datetime import datetime, timedelta

def page_linkedin_analysis(posts_df, metrics_df):
    st.title("🔗 LinkedIn Analysis")
    st.markdown("Comprehensive analytics for LinkedIn performance")
    
    # Metrics section
    if metrics_df is not None and not metrics_df.empty:
        st.header("📊 Performance Metrics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if "Impressions (total)" in metrics_df.columns:
                total_impressions = metrics_df["Impressions (total)"].sum()
                prev_impressions = total_impressions * 0.95  # Simulate 5% growth
                delta = ((total_impressions - prev_impressions) / prev_impressions) * 100
                display_metric("Total Impressions", f"{total_impressions:,}", delta)
            else:
                st.warning("Impressions data not available")
            
        with col2:
            if "Clicks (total)" in metrics_df.columns:
                total_clicks = metrics_df["Clicks (total)"].sum()
                prev_clicks = total_clicks * 0.93  # Simulate 7% growth
                delta = ((total_clicks - prev_clicks) / prev_clicks) * 100
                display_metric("Total Clicks", f"{total_clicks:,}", delta)
            else:
                st.warning("Clicks data not available")
            
        with col3:
            if "Engagement rate (total)" in metrics_df.columns:
                avg_engagement = metrics_df["Engagement rate (total)"].mean()
                prev_engagement = avg_engagement * 0.98  # Simulate 2% growth
                delta = ((avg_engagement - prev_engagement) / prev_engagement) * 100
                display_metric("Avg Engagement", f"{avg_engagement:.2f}%", delta)
            else:
                st.warning("Engagement data not available")

        # Time series charts
        st.subheader("Performance Over Time")
        tab1, tab2, tab3 = st.tabs(["Impressions", "Engagement", "Breakdown"])
        
        with tab1:
            if all(col in metrics_df.columns for col in ["Date", "Impressions (organic)", "Impressions (sponsored)"]):
                fig = px.line(metrics_df, x="Date", y=["Impressions (organic)", "Impressions (sponsored)"],
                             title="Organic vs Sponsored Impressions")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Impressions time series data not available")
                
        with tab2:
            if all(col in metrics_df.columns for col in ["Date", "Engagement rate (organic)", "Engagement rate (sponsored)"]):
                fig = px.line(metrics_df, x="Date", y=["Engagement rate (organic)", "Engagement rate (sponsored)"],
                             title="Organic vs Sponsored Engagement")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Engagement time series data not available")
                
        with tab3:
            if all(col in metrics_df.columns for col in ["Date", "Clicks (organic)", "Clicks (sponsored)"]):
                fig = px.bar(metrics_df, x="Date", y=["Clicks (organic)", "Clicks (sponsored)"],
                            title="Organic vs Sponsored Clicks", barmode='stack')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Clicks breakdown data not available")

    # Posts analysis section
    if posts_df is not None and not posts_df.empty:
        st.header("📄 Post Performance")
        
        # Top posts section
        st.subheader("Top Performing Posts")
        if "Engagement rate" in posts_df.columns:
            top_posts = posts_df.nlargest(5, "Engagement rate")
            display_cols = [col for col in ["Post title", "Post type", "Created date", "Impressions", "Engagement rate"] 
                          if col in posts_df.columns]
            st.dataframe(top_posts[display_cols])
        else:
            st.warning("Engagement rate data not available for posts")
        
        # Post type analysis
        st.subheader("Post Type Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            if "Post type" in posts_df.columns:
                post_types = posts_df["Post type"].value_counts().reset_index()
                fig = px.pie(post_types, values="count", names="Post type",
                            title="Post Type Distribution")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Post type data not available")
                
        with col2:
            if all(col in posts_df.columns for col in ["Post type", "Engagement rate"]):
                post_type_perf = posts_df.groupby("Post type").agg({
                    "Engagement rate": "mean",
                    "Impressions": "mean" if "Impressions" in posts_df.columns else None
                }).reset_index()
                fig = px.bar(post_type_perf, x="Post type", y="Engagement rate",
                            title="Engagement by Post Type")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Post type performance data not available")
        
        # Campaign analysis if available
        if "Campaign name" in posts_df.columns:
            st.subheader("Campaign Performance")
            if all(col in posts_df.columns for col in ["Campaign name", "Impressions", "Engagement rate"]):
                campaign_stats = posts_df.groupby("Campaign name").agg({
                    "Impressions": "sum",
                    "Engagement rate": "mean"
                }).reset_index()
                
                fig = px.bar(campaign_stats, x="Campaign name", y="Impressions",
                            title="Impressions by Campaign")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Campaign performance data not complete")