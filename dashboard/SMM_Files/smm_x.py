import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_x(x_data):
    st.title("🐦 X (Twitter) Metrics")
    st.markdown("Detailed analytics for X (Twitter) performance")

    if x_data is None or x_data.empty:
        st.warning("No X (Twitter) data available")
        return

    st.header("📊 Engagement Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_tweets = len(x_data)
        display_metric("Total Tweets", total_tweets, 0)
    with col2:
        total_impressions = x_data["Impressions"].sum()
        display_metric("Total Impressions", f"{total_impressions:,}", 0)
    with col3:
        total_engagements = x_data["Engagements"].sum()
        display_metric("Total Engagements", f"{total_engagements:,}", 0)

    st.subheader("Engagement Over Time")
    x_data["Date"] = pd.to_datetime(x_data["Date"]).dt.date
    engagement_trend = x_data.groupby("Date")["Engagements"].sum().reset_index()
    fig = px.line(engagement_trend, x="Date", y="Engagements",
                 title="Daily Engagement Trend")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Performing Tweets")
    top_tweets = x_data.nlargest(5, "Engagements")
    st.dataframe(top_tweets[["Date", "Tweet text", "Impressions", "Engagements"]])