import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_retention(retention_data):
    st.title("📈 Retention & Cohorts")
    st.markdown("This page shows user retention and cohort analysis.")

    if retention_data is None or retention_data.empty:
        st.warning("No retention & cohorts data available.")
        return

    st.header("📊 Retention Metrics")
    col1, col2 = st.columns(2)
    with col1:
        avg_retention = retention_data["retentionRate"].mean()
        display_metric("Avg Retention Rate", f"{avg_retention:.1f}%", 0)
    with col2:
        total_retained = retention_data["retainedUsers"].sum()
        display_metric("Total Retained Users", f"{total_retained:,}", 0)

    st.subheader("Retention by Cohort")
    cohort_data = retention_data.groupby("cohort").agg({
        "retentionRate": "mean",
        "retainedUsers": "sum"
    }).reset_index()

    fig = px.bar(cohort_data, x="cohort", y="retentionRate",
                title="Retention Rate by Cohort")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Retained Users by Cohort")
    fig = px.line(cohort_data, x="cohort", y="retainedUsers",
                 title="Retained Users by Cohort", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    if "date" in retention_data.columns:
        st.subheader("Retention Trends Over Time")
        time_data = retention_data.groupby("date")["retentionRate"].mean().reset_index()
        fig = px.line(time_data, x="date", y="retentionRate",
                     title="Daily Retention Rate Trend")
        st.plotly_chart(fig, use_container_width=True)