import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_youtube(youtube_data):
    st.title("📺 YouTube Metrics")
    st.markdown("Detailed analytics for YouTube performance")

    if youtube_data is None or youtube_data.empty:
        st.warning("No YouTube data available")
        return

    st.header("📊 Video Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_views = youtube_data["Views"].sum()
        display_metric("Total Views", f"{total_views:,}", 0)
    with col2:
        total_watch_time = youtube_data["Watch time (minutes)"].sum()
        display_metric("Total Watch Time", f"{total_watch_time:,} mins", 0)
    with col3:
        avg_duration = youtube_data["Average view duration"].mean()
        display_metric("Avg View Duration", f"{avg_duration:.1f} mins", 0)

    st.subheader("Views Over Time")
    youtube_data["Date"] = pd.to_datetime(youtube_data["Date"]).dt.date
    views_trend = youtube_data.groupby("Date")["Views"].sum().reset_index()
    fig = px.line(views_trend, x="Date", y="Views",
                 title="Daily Views Trend")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Performing Videos")
    top_videos = youtube_data.nlargest(5, "Views")
    st.dataframe(top_videos[["Title", "Views", "Watch time (minutes)", "Likes"]])