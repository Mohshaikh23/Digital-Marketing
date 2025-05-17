import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_smm_overview(facebook_data, instagram_data, linkedin_metrics, linkedin_posts, youtube_data, x_data):
    st.title("📊 Social Media Overview")
    st.markdown("Comprehensive view of all social media performance metrics.")

    def safe_sum(df, col_names, default=0):
        for col in col_names:
            if col in df.columns:
                return df[col].sum()
        return default

    st.header("📈 Platform Comparison")
    platforms = []
    metrics = []
    
    # Facebook metrics
    if facebook_data is not None and not facebook_data.empty:
        platforms.append("Facebook")
        metrics.append({
            "Posts": len(facebook_data),
            "Engagement": safe_sum(facebook_data, ["Reactions, comments and shares", "Engagement"]),
            "Reach": safe_sum(facebook_data, ["Reach", "Total reach"])
        })
    
    # Instagram metrics
    if instagram_data is not None and not instagram_data.empty:
        platforms.append("Instagram")
        metrics.append({
            "Posts": len(instagram_data),
            "Engagement": safe_sum(instagram_data, ["Likes", "Engagement"]),
            "Reach": safe_sum(instagram_data, ["Reach", "Total reach"])
        })
    
    # LinkedIn metrics
    if linkedin_metrics is not None and not linkedin_metrics.empty:
        platforms.append("LinkedIn")
        metrics.append({
            "Posts": len(linkedin_posts) if linkedin_posts is not None else 0,
            "Engagement": linkedin_metrics["Engagement rate (total)"].mean() if "Engagement rate (total)" in linkedin_metrics.columns else 0,
            "Reach": safe_sum(linkedin_metrics, ["Impressions (total)", "Total impressions"])
        })
    
    # Create comparison dataframe
    if platforms:
        comparison_df = pd.DataFrame(metrics, index=platforms)
        
        st.subheader("Engagement by Platform")
        fig = px.bar(comparison_df, x=comparison_df.index, y="Engagement",
                    title="Total Engagement by Platform")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Reach by Platform")
        fig = px.pie(comparison_df, values="Reach", names=comparison_df.index,
                    title="Reach Distribution Across Platforms")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No social media data available for comparison")

    st.header("📅 Recent Activity")
    if linkedin_posts is not None and not linkedin_posts.empty:
        st.subheader("Latest LinkedIn Posts")
        st.dataframe(linkedin_posts[["Created date", "Post title", "Impressions"]].head(5))
    
    if facebook_data is not None and not facebook_data.empty:
        st.subheader("Latest Facebook Posts")
        st.dataframe(facebook_data[["Publish time", "Title", "Reach"]].head(5))