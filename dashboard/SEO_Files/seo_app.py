import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_app(app_data):
    st.title("📱 App-Specific Data")
    st.markdown("This page shows the performance of your app.")

    if app_data is None or app_data.empty:
        st.warning("No app-specific data available.")
        return

    st.header("📊 App Performance Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        if "screenPageViews" in app_data.columns:
            total_views = app_data["screenPageViews"].sum()
            display_metric("Total Screen Views", f"{total_views:,}", 0)
    with col2:
        if "userEngagementDuration" in app_data.columns:
            total_engagement = app_data["userEngagementDuration"].sum()
            display_metric("Total Engagement", f"{total_engagement:,.1f} mins", 0)
    with col3:
        if "appVersion" in app_data.columns:
            unique_versions = app_data["appVersion"].nunique()
            display_metric("App Versions", unique_versions, 0)

    if "appVersion" in app_data.columns and "screenPageViews" in app_data.columns:
        st.subheader("Screen Views by App Version")
        version_data = app_data.groupby("appVersion")["screenPageViews"].sum().reset_index()
        fig = px.bar(version_data, x="appVersion", y="screenPageViews", 
                     title="Screen Views by App Version")
        st.plotly_chart(fig, use_container_width=True)

    if "platform" in app_data.columns and "userEngagementDuration" in app_data.columns:
        st.subheader("User Engagement by Platform")
        platform_data = app_data.groupby("platform")["userEngagementDuration"].sum().reset_index()
        fig = px.pie(platform_data, values="userEngagementDuration", names="platform", 
                     title="User Engagement by Platform")
        st.plotly_chart(fig, use_container_width=True)

    if "date" in app_data.columns:
        st.subheader("Daily Active Users")
        daily_users = app_data.groupby("date")["activeUsers"].sum().reset_index()
        fig = px.line(daily_users, x="date", y="activeUsers", 
                      title="Daily Active Users Trend")
        st.plotly_chart(fig, use_container_width=True)