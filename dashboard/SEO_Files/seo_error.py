import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_error_tracking(error_data):
    st.title("❌ Error Tracking")
    st.markdown("This page shows errors encountered by users.")

    if error_data is None or error_data.empty:
        st.warning("No error tracking data available.")
        return

    st.header("📊 Error Overview")
    col1, col2 = st.columns(2)
    with col1:
        total_errors = error_data["eventCount"].sum()
        display_metric("Total Errors", total_errors, 0)
    with col2:
        unique_errors = error_data["eventName"].nunique()
        display_metric("Unique Error Types", unique_errors, 0)

    st.subheader("Error Distribution")
    error_counts = error_data.groupby("eventName")["eventCount"].sum().reset_index()
    fig = px.pie(error_counts, values="eventCount", names="eventName",
                title="Error Distribution by Type")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Most Common Errors")
    fig = px.bar(error_counts.sort_values("eventCount", ascending=False).head(10),
                x="eventName", y="eventCount",
                title="Top 10 Error Types")
    st.plotly_chart(fig, use_container_width=True)

    if "date" in error_data.columns:
        st.subheader("Error Trends Over Time")
        time_data = error_data.groupby("date")["eventCount"].sum().reset_index()
        fig = px.line(time_data, x="date", y="eventCount",
                     title="Daily Error Count Trend")
        st.plotly_chart(fig, use_container_width=True)