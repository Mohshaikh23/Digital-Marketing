import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_instagram(instagram_data):
    st.title("📸 Instagram Metrics")
    st.markdown("Detailed analytics for Instagram performance")

    if instagram_data is None or instagram_data.empty:
        st.warning("No Instagram data available")
        return

    st.header("📊 Engagement Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_posts = len(instagram_data)
        display_metric("Total Posts", total_posts, 0)
    with col2:
        total_likes = instagram_data["Likes"].sum()
        display_metric("Total Likes", f"{total_likes:,}", 0)
    with col3:
        total_comments = instagram_data["Comments"].sum()
        display_metric("Total Comments", f"{total_comments:,}", 0)

    st.subheader("Engagement Over Time")
    instagram_data["Date"] = pd.to_datetime(instagram_data["Date"]).dt.date
    engagement_trend = instagram_data.groupby("Date")["Likes"].sum().reset_index()
    fig = px.line(engagement_trend, x="Date", y="Likes",
                 title="Daily Likes Trend")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Performing Posts")
    top_posts = instagram_data.nlargest(5, "Likes")
    st.dataframe(top_posts[["Date", "Caption", "Likes", "Comments"]])

    st.header("📈 Content Analysis")
    if "Media Type" in instagram_data.columns:
        media_types = instagram_data["Media Type"].value_counts().reset_index()
        fig = px.pie(media_types, values="count", names="Media Type",
                    title="Media Type Distribution")
        st.plotly_chart(fig, use_container_width=True)