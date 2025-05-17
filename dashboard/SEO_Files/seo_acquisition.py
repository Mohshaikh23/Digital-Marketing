import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_acquisition(acquisition_data):
    st.title("📈 Acquisition")
    st.markdown("This page shows where your users are coming from.")

    if acquisition_data is not None and not acquisition_data.empty:
        # Metric: Top Traffic Source
        top_source = acquisition_data.groupby("sessionSource")["sessions"].sum().idxmax()
        st.metric("Top Traffic Source", top_source)

        # Pie chart: Traffic Sources
        st.subheader("Traffic Sources")
        source_data = acquisition_data.groupby("sessionSource")["sessions"].sum().reset_index()
        fig = px.pie(source_data, values="sessions", names="sessionSource", title="Traffic Sources")
        st.plotly_chart(fig, use_container_width=True)

        # Time-based acquisition trends
        if "date" in acquisition_data.columns:
            st.subheader("Acquisition Trends Over Time")
            time_data = acquisition_data.groupby(["date", "sessionSource"])["sessions"].sum().reset_index()
            fig = px.line(time_data, x="date", y="sessions", color="sessionSource",
                          title="Acquisition Trends by Source")
            st.plotly_chart(fig, use_container_width=True)

        # Medium breakdown
        if "sessionMedium" in acquisition_data.columns:
            st.subheader("Traffic Mediums")
            medium_data = acquisition_data.groupby("sessionMedium")["sessions"].sum().reset_index()
            fig = px.bar(medium_data, x="sessionMedium", y="sessions", 
                         title="Traffic by Medium", color="sessionMedium")
            st.plotly_chart(fig, use_container_width=True)