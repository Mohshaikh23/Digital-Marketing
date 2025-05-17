import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_calendar import calendar
from Shared_Components.components import display_metric

def show_social_media_calendar(facebook_data, instagram_data, linkedin_posts):
    st.title("📅 Social Media Calendar")
    st.markdown("Visualization of all social media posts across platforms")

    events = []
    platform_colors = {
        "Facebook": "#1877F2",
        "Instagram": "#E1306C",
        "LinkedIn": "#0077B5"
    }

    # Helper function to get column with fallbacks
    def get_column(row, possible_names, default=""):
        for name in possible_names:
            if name in row:
                return row[name]
        return default

    # Process Facebook Posts
    if facebook_data is not None and not facebook_data.empty:
        for _, row in facebook_data.iterrows():
            events.append({
                "title": f"Facebook: {get_column(row, ['Title', 'Post title', 'Post Title'], 'Untitled Post')}",
                "start": pd.to_datetime(row["Publish time"]).strftime("%Y-%m-%dT%H:%M:%S"),
                "color": platform_colors["Facebook"],
                "extendedProps": {
                    "platform": "Facebook",
                    "metrics": {
                        "Reach": get_column(row, ["Reach", "Total reach"]),
                        "Engagement": get_column(row, ["Reactions, comments and shares", "Engagement"]),
                        "Clicks": get_column(row, ["Total clicks", "Clicks"])
                    }
                }
            })

    # Process Instagram Posts
    if instagram_data is not None and not instagram_data.empty:
        for _, row in instagram_data.iterrows():
            if row["Date"] == "Lifetime":
                continue
            events.append({
                "title": f"Instagram: {get_column(row, ['Title', 'Post title', 'Post Title'], 'Untitled Post')}",
                "start": pd.to_datetime(row["Date"]).strftime("%Y-%m-%dT%H:%M:%S"),
                "color": platform_colors["Instagram"],
                "extendedProps": {
                    "platform": "Instagram",
                    "metrics": {
                        "Reach": get_column(row, ["Reach", "Total reach"]),
                        "Engagement": get_column(row, ["Likes", "Engagement"]),
                        "Clicks": get_column(row, ["Total clicks", "Clicks"])
                    }
                }
            })

    # Process LinkedIn Posts
    if linkedin_posts is not None and not linkedin_posts.empty:
        # st.sidebar.write("LinkedIn columns:", linkedin_posts.columns.tolist())  # Debug info
        
        for _, row in linkedin_posts.iterrows():
            events.append({
                "title": f"LinkedIn: {get_column(row, ['Post title', 'Title', 'Post Title', 'Post name'], 'Untitled Post')}",
                "start": pd.to_datetime(get_column(row, ['Created date', 'Date', 'Post date'])).strftime("%Y-%m-%dT%H:%M:%S"),
                "color": platform_colors["LinkedIn"],
                "extendedProps": {
                    "platform": "LinkedIn",
                    "metrics": {
                        "Impressions": get_column(row, ["Impressions", "Total impressions"]),
                        "Engagement": get_column(row, ["Engagement rate", "Engagement"]),
                        "Clicks": get_column(row, ["Clicks", "Total clicks"])
                    }
                }
            })

    if events:
        calendar_options = {
            "editable": False,
            "selectable": True,
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            }
        }

        calendar_result = calendar(events=events, options=calendar_options)

        if calendar_result.get("eventClick"):
            selected_event = calendar_result["eventClick"]["event"]
            st.write(f"**Selected Post:** {selected_event['title']}")
            st.write(f"**Platform:** {selected_event['extendedProps']['platform']}")
            st.write(f"**Date:** {selected_event['start']}")

            st.write("### Post Performance Metrics")
            for metric_name, metric_value in selected_event["extendedProps"]["metrics"].items():
                st.write(f"**{metric_name}:** {metric_value if metric_value else 'N/A'}")
    else:
        st.warning("No social media posts available for calendar view")