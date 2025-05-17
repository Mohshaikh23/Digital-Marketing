import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_site_speed(site_speed_data):
    st.title("⏱️ Site Speed & Performance")
    st.markdown("This page shows the performance of your website.")

    if site_speed_data is None or site_speed_data.empty:
        st.warning("No site speed & performance data available.")
        return

    st.header("🚀 Performance Metrics")
    col1, col2 = st.columns(2)
    with col1:
        if "averageSessionDuration" in site_speed_data.columns:
            avg_duration = site_speed_data["averageSessionDuration"].mean()
            display_metric("Avg Session Duration", f"{avg_duration:.2f} sec", 0)
    with col2:
        if "pageLoadTime" in site_speed_data.columns:
            avg_load_time = site_speed_data["pageLoadTime"].mean()
            display_metric("Avg Page Load Time", f"{avg_load_time:.2f} sec", 0)

    if "pagePath" in site_speed_data.columns:
        st.subheader("Performance by Page")
        if "averageSessionDuration" in site_speed_data.columns:
            page_duration = site_speed_data.groupby("pagePath")["averageSessionDuration"].mean().reset_index()
            fig = px.bar(page_duration.sort_values("averageSessionDuration", ascending=False).head(10),
                         x="pagePath", y="averageSessionDuration",
                         title="Average Session Duration by Page")
            st.plotly_chart(fig, use_container_width=True)

        if "pageLoadTime" in site_speed_data.columns:
            page_load = site_speed_data.groupby("pagePath")["pageLoadTime"].mean().reset_index()
            fig = px.bar(page_load.sort_values("pageLoadTime").head(10),
                         x="pagePath", y="pageLoadTime",
                         title="Fastest Loading Pages")
            st.plotly_chart(fig, use_container_width=True)

    if "date" in site_speed_data.columns:
        st.subheader("Performance Trends Over Time")
        if "averageSessionDuration" in site_speed_data.columns:
            time_data = site_speed_data.groupby("date")["averageSessionDuration"].mean().reset_index()
            fig = px.line(time_data, x="date", y="averageSessionDuration",
                         title="Average Session Duration Over Time")
            st.plotly_chart(fig, use_container_width=True)