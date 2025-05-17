import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_funnel(funnel_data):
    st.title("📊 Funnel Analysis")
    st.markdown("This page shows the performance of your conversion funnel.")

    if funnel_data is None or funnel_data.empty:
        st.warning("No funnel analysis data available.")
        return

    st.header("🚀 Funnel Overview")
    col1, col2 = st.columns(2)
    with col1:
        total_conversions = funnel_data["funnelConversions"].sum()
        display_metric("Total Conversions", total_conversions, 0)
    with col2:
        avg_dropoff = funnel_data["funnelDropOffRate"].mean()
        display_metric("Avg Drop-off Rate", f"{avg_dropoff:.1f}%", 0)

    st.subheader("Funnel Visualization")
    funnel_steps = funnel_data.groupby("funnelStep").agg({
        "funnelConversions": "sum",
        "funnelDropOffRate": "mean"
    }).reset_index().sort_values("funnelStep")

    fig = px.funnel(funnel_steps, x="funnelConversions", y="funnelStep",
                   title="Conversion Funnel")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Drop-off Rate by Step")
    fig = px.line(funnel_steps, x="funnelStep", y="funnelDropOffRate",
                 title="Drop-off Rate by Funnel Step", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    if "date" in funnel_data.columns:
        st.subheader("Funnel Performance Over Time")
        time_data = funnel_data.groupby(["date", "funnelStep"])["funnelConversions"].sum().reset_index()
        fig = px.line(time_data, x="date", y="funnelConversions", color="funnelStep",
                     title="Daily Funnel Conversions by Step")
        st.plotly_chart(fig, use_container_width=True)