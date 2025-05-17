import streamlit as st
st.set_page_config(page_title="Digital Marketing & SEO Dashboard", layout="wide")

import statsmodels.api as sm
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import plotly.express as px
from streamlit_calendar import calendar
from data_loader import (
    connect_to_google_sheets,
    load_sheet_data,
    validate_data,
    filter_data_by_date,
    load_social_media_data_from_sheet,
    load_linkedin_data,
    load_facebook_data,
    load_instagram_data,
    calculate_growth,
    calculate_delta,
    calculate_post_metrics
)
import numpy as np
from data_extractor import refresh_data
from sklearn.linear_model import LinearRegression


# Complete worksheet name mapping with alternatives
WORKSHEET_MAPPING = {
    # SEO/GA4 Data
    "user_traffic": {
        "primary": "user_traffic",
        "alternatives": [],
        "required_cols": ["date", "totalUsers", "activeUsers", "sessions", "bounceRate"]
    },
    "engagement": {
        "primary": "engagement", 
        "alternatives": [],
        "required_cols": ["date", "averageSessionDuration", "screenPageViewsPerSession", "eventCount"]
    },
    "acquisition": {
        "primary": "acquisition",
        "alternatives": [],
        "required_cols": ["date", "sessionSource", "sessionMedium", "sessions", "totalUsers"]
    },
    "page_views": {
        "primary": "page_views",
        "alternatives": [],
        "required_cols": ["date", "pageTitle", "screenPageViews", "screenPageViewsPerSession"]
    },
    "demographics": {
        "primary": "demographics",
        "alternatives": [],
        "required_cols": ["date", "country", "activeUsers","userAgeBracket", "userGender"]
    },
    "device": {
        "primary": "technology",
        "alternatives": [],
        "required_cols": ["date", "deviceCategory", "operatingSystem", "browser"]
    },
    "events": {
        "primary": "events",
        "alternatives": [],
        "required_cols": ["date", "eventName", "eventCount"]
    },
    "site_speed": {
        "primary": "site_speed",
        "alternatives": [],
        "required_cols": ["date", "pagePath", "averageSessionDuration"]
    },
     "audience": {
        "primary": "audience",
        "alternatives": ["audience_segments", "user_segments"],
        "required_cols": ["audienceName", "activeUsers", "conversions"]
    },
    
    
    # SEO Data
    "search_console": {
        "primary": "seo_top_queries",
        "alternatives": [],
        "required_cols": ["clicks", "impressions", "position", "ctr"]
    },
    "seo_pages": {
        "primary": "seo_top_pages",
        "alternatives": [],
        "required_cols": ["clicks", "impressions", "position"]
    },
    "seo_content": {
        "primary": "seo_content_engagement",
        "alternatives": [],
        "required_cols": ["screenPageViews", "engagementRate"]
    },
    "organic_search": {
        "primary": "organic_search",
        "alternatives": [],
        "required_cols": ["date", "firstUserSource", "firstUserMedium", "sessions"]
    },
    "landing_pages": {
        "primary": "seo_landing_pages",
        "alternatives": [],
        "required_cols": ["date", "landingPage", "sessionSource", "sessions"]
    }
}



# Function to display a metric with a colored delta
def display_metric(label, value, delta_value):
    if delta_value > 0:
        delta_color = "green"
        delta_sign = f"↑ {delta_value:.2f}%"
    elif delta_value < 0:
        delta_color = "red"
        delta_sign = f"↓ {abs(delta_value):.2f}%"
    else:
        delta_color = "gray"
        delta_sign = f"→ {delta_value:.2f}%"
    
    st.markdown(f"""
        <div class="metric-box">
            <strong>{label}</strong><br>
            {value}<br>
            <span style="color: {delta_color};">{delta_sign}</span>
        </div>
    """, unsafe_allow_html=True)

# Add custom CSS for metric borders
st.markdown("""
    <style>
    .metric-box {
        border: 2px solid #e1e4e8;
        border-radius: 10px;
        padding: 10px;
        background-color: #f9f9f9;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


def show_social_media_calendar(facebook_data, instagram_data, linkedin_posts):
    # Initialize an empty list to store events
    events = []

    # Define platform-specific colors
    platform_colors = {
        "Facebook": "#1877F2",  # Facebook blue
        "Instagram": "#E1306C",  # Instagram pink
        "LinkedIn": "#0077B5",  # LinkedIn blue
    }

    # Helper function to clean metrics
    def clean_metrics(metrics):
        cleaned_metrics = {}
        for key, value in metrics.items():
            if pd.isna(value):  # Replace NaN with "N/A"
                cleaned_metrics[key] = "N/A"
            else:
                cleaned_metrics[key] = value
        return cleaned_metrics

    # Process Facebook Posts
    if facebook_data is not None and not facebook_data.empty:
        for _, row in facebook_data.iterrows():
            event = {
                "title": row["Title"],
                "start": pd.to_datetime(row["Publish time"]).strftime("%Y-%m-%dT%H:%M:%S"),
                "end": pd.to_datetime(row["Publish time"]).strftime("%Y-%m-%dT%H:%M:%S"),
                "color": platform_colors["Facebook"],  # Facebook color
                "extendedProps": {
                    "platform": "Facebook",
                    "metrics": clean_metrics({
                        "Reach": row.get("Reach"),
                        "Engagement": row.get("Reactions, comments and shares"),
                        "Clicks": row.get("Total clicks"),
                        "Negative Feedback": row.get("Negative feedback from users"),
                    }),
                },
            }
            events.append(event)

    # Process Instagram Posts
    if instagram_data is not None and not instagram_data.empty:
        for _, row in instagram_data.iterrows():
            # Handle "Lifetime" values by skipping them
            if row["Date"] == "Lifetime":
                continue
            event = {
                "title": row["Title"],
                "start": pd.to_datetime(row["Date"]).strftime("%Y-%m-%dT%H:%M:%S"),
                "end": pd.to_datetime(row["Date"]).strftime("%Y-%m-%dT%H:%M:%S"),
                "color": platform_colors["Instagram"],  # Instagram color
                "extendedProps": {
                    "platform": "Instagram",
                    "metrics": clean_metrics({
                        "Reach": row.get("Reach"),
                        "Engagement": row.get("Reactions, comments and shares"),
                        "Clicks": row.get("Total clicks"),
                        "Negative Feedback": row.get("Negative feedback from users"),
                    }),
                },
            }
            events.append(event)

    # Process LinkedIn Posts
    if linkedin_posts is not None and not linkedin_posts.empty:
        # Debug: Print column names to verify
        print("LinkedIn Posts Columns:", linkedin_posts.columns)

        # Check if required columns exist
        required_columns = ["Created date", "Post title"]
        if all(col in linkedin_posts.columns for col in required_columns):
            for _, row in linkedin_posts.iterrows():
                event = {
                    "title": row["Post title"],
                    "start": pd.to_datetime(row["Created date"]).strftime("%Y-%m-%dT%H:%M:%S"),
                    "end": pd.to_datetime(row["Created date"]).strftime("%Y-%m-%dT%H:%M:%S"),
                    "color": platform_colors["LinkedIn"],  # LinkedIn color
                    "extendedProps": {
                        "platform": "LinkedIn",
                        "metrics": clean_metrics({
                            "Impressions": row.get("Impressions"),
                            "Clicks": row.get("Clicks"),
                            "Engagement Rate": row.get("Engagement rate"),
                            "Likes": row.get("Likes"),
                            "Comments": row.get("Comments"),
                            "Reposts": row.get("Reposts"),
                        }),
                    },
                }
                events.append(event)
        else:
            print("⚠️ Required columns not found in LinkedIn posts data. Skipping LinkedIn data.")

    # Display the Calendar
    if events:
        # Configure the calendar
        calendar_options = {
            "editable": False,  # Disable editing
            "selectable": True,  # Allow selecting dates
            "initialView": "dayGridMonth",  # Default view: month
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay",
            },
        }

        # Render the calendar
        st.write("## Social Media Posting Calendar")
        calendar_result = calendar(events=events, options=calendar_options)

        # Display selected event details
        if calendar_result.get("eventClick"):
            selected_event = calendar_result["eventClick"]["event"]
            st.write(f"**Selected Post:** {selected_event['title']}")
            st.write(f"**Platform:** {selected_event['extendedProps']['platform']}")
            st.write(f"**Date:** {selected_event['start']}")

            # Display metrics
            st.write("### Post Performance Metrics")
            metrics = selected_event["extendedProps"]["metrics"]
            for metric_name, metric_value in metrics.items():
                st.write(f"**{metric_name}:** {metric_value}")
    else:
        st.warning("⚠️ No social media posts available for calendar view.")

# Page 1: Overview
def page_overview(user_traffic_data, engagement_data, conversion_data):
    st.title("📊 Overview")
    st.markdown("""
        Welcome to the **Digital Marketing & SEO Dashboard**!  
        This page provides a high-level overview of your website's performance.
    """)

    if user_traffic_data is not None and not user_traffic_data.empty:
        st.header("🚦 User & Traffic Data")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_users = user_traffic_data["totalUsers"].sum()
            previous_total_users = user_traffic_data["totalUsers"].shift(7).sum()  # WoW comparison
            delta_users = calculate_delta(total_users, previous_total_users)
            display_metric("Total Users", total_users, delta_users)
        with col2:
            avg_bounce_rate = user_traffic_data["bounceRate"].mean()
            previous_bounce_rate = user_traffic_data["bounceRate"].shift(7).mean()  # WoW comparison
            delta_bounce_rate = calculate_delta(avg_bounce_rate, previous_bounce_rate)
            display_metric("Average Bounce Rate", f"{avg_bounce_rate:.2f}%", delta_bounce_rate)
        with col3:
            total_sessions = user_traffic_data["sessions"].sum()
            previous_sessions = user_traffic_data["sessions"].shift(7).sum()  # WoW comparison
            delta_sessions = calculate_delta(total_sessions, previous_sessions)
            display_metric("Total Sessions", total_sessions, delta_sessions)

        # Column chart: Active Users Over Time
        st.subheader("Active Users Over Time")
        fig = px.bar(user_traffic_data, x="date", y="activeUsers", title="Active Users Over Time")
        st.plotly_chart(fig, use_container_width=True)

    if engagement_data is not None and not engagement_data.empty:
        st.header("🎯 User Engagement & Behavior")
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_session_duration = engagement_data["averageSessionDuration"].mean()
            previous_session_duration = engagement_data["averageSessionDuration"].shift(7).mean()  # WoW comparison
            delta_session_duration = calculate_delta(avg_session_duration, previous_session_duration)
            display_metric("Average Session Duration", f"{avg_session_duration:.2f} seconds", delta_session_duration)
        with col2:
            avg_pages_per_session = engagement_data["screenPageViewsPerSession"].mean()
            previous_pages_per_session = engagement_data["screenPageViewsPerSession"].shift(7).mean()  # WoW comparison
            delta_pages_per_session = calculate_delta(avg_pages_per_session, previous_pages_per_session)
            display_metric("Average Pages per Session", f"{avg_pages_per_session:.2f}", delta_pages_per_session)
        with col3:
            total_events = engagement_data["eventCount"].sum()
            previous_events = engagement_data["eventCount"].shift(7).sum()  # WoW comparison
            delta_events = calculate_delta(total_events, previous_events)
            display_metric("Total Events", total_events, delta_events)

        # Column chart: Event Count Over Time
        st.subheader("Event Count Over Time")
        fig = px.bar(engagement_data, x="date", y="eventCount", title="Event Count Over Time")
        st.plotly_chart(fig, use_container_width=True)

    if conversion_data is not None and not conversion_data.empty:
        st.header("💰 Conversion & Goal Tracking")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_conversions = conversion_data["conversions"].sum()
            previous_conversions = conversion_data["conversions"].shift(7).sum()  # WoW comparison
            delta_conversions = calculate_delta(total_conversions, previous_conversions)
            display_metric("Total Conversions", total_conversions, delta_conversions)
        with col2:
            total_revenue = conversion_data["totalRevenue"].sum()
            previous_revenue = conversion_data["totalRevenue"].shift(7).sum()  # WoW comparison
            delta_revenue = calculate_delta(total_revenue, previous_revenue)
            display_metric("Total Revenue", f"${total_revenue:,.2f}", delta_revenue)
        with col3:
            conversion_rate = (total_conversions / total_users) * 100
            previous_conversion_rate = (previous_conversions / previous_total_users) * 100  # WoW comparison
            delta_conversion_rate = calculate_delta(conversion_rate, previous_conversion_rate)
            display_metric("Conversion Rate", f"{conversion_rate:.2f}%", delta_conversion_rate)

        # Column chart: Conversions Over Time
        st.subheader("Conversions Over Time")
        fig = px.bar(conversion_data, x="date", y="conversions", title="Conversions Over Time")
        st.plotly_chart(fig, use_container_width=True)

# Page 2: Acquisition
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

# Page 3: Page Views
def page_page_views(page_views_data):
    st.title("📄 Page Views Analysis")
    st.markdown("""
        This page provides comprehensive insights into your website's page performance, 
        including traffic patterns, engagement metrics, and content effectiveness.
    """)

    if page_views_data is None or page_views_data.empty:
        st.warning("No page views data available.")
        return

    # Check available columns
    available_cols = page_views_data.columns.tolist()
    
    # 1. Top Pages Overview
    st.header("🚀 Top Performing Pages")
    
    # Determine time period for comparison
    if "date" in available_cols:
        page_views_data["date"] = pd.to_datetime(page_views_data["date"])
        min_date = page_views_data["date"].min()
        max_date = page_views_data["date"].max()
        time_period = (max_date - min_date).days
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_views = page_views_data["screenPageViews"].sum()
            display_metric("Total Page Views", f"{total_views:,}", 0)
            
        with col2:
            avg_views_per_day = total_views / time_period if time_period > 0 else 0
            display_metric("Avg Views/Day", f"{avg_views_per_day:,.1f}", 0)
            
        with col3:
            unique_pages = page_views_data["pageTitle"].nunique()
            display_metric("Unique Pages", unique_pages, 0)
    
    # 2. Top Pages Analysis
    st.subheader("📊 Page Performance Metrics")
    
    # Group by page and calculate metrics
    page_stats = page_views_data.groupby("pageTitle").agg({
        "screenPageViews": ["sum", "mean", "std"],
        "screenPageViewsPerSession": ["mean", "median"]
    }).reset_index()
    
    # Flatten multi-index columns
    page_stats.columns = ['_'.join(col).strip() if col[1] else col[0] 
                         for col in page_stats.columns.values]
    
    # Rename columns for clarity
    page_stats = page_stats.rename(columns={
        "screenPageViews_sum": "total_views",
        "screenPageViews_mean": "avg_daily_views",
        "screenPageViews_std": "views_std_dev",
        "screenPageViewsPerSession_mean": "avg_views_per_session",
        "screenPageViewsPerSession_median": "median_views_per_session"
    })
    
    # Display top pages in tabs
    tab1, tab2, tab3 = st.tabs(["By Total Views", "By Engagement", "Raw Data"])
    
    with tab1:
        st.subheader("Top 10 Pages by Total Views")
        top_pages = page_stats.sort_values("total_views", ascending=False).head(10)
        fig = px.bar(top_pages, x="pageTitle", y="total_views", 
                     color="total_views", title="Top Pages by Total Views")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show consistency of top performers
        st.subheader("View Consistency of Top Pages")
        fig = px.scatter(top_pages, x="avg_daily_views", y="views_std_dev",
                         size="total_views", hover_name="pageTitle",
                         title="Daily View Consistency (Size = Total Views)")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Top 10 Pages by Engagement")
        engaged_pages = page_stats.sort_values("avg_views_per_session", ascending=False).head(10)
        fig = px.bar(engaged_pages, x="pageTitle", y="avg_views_per_session", 
                     color="avg_views_per_session", title="Top Pages by Views Per Session")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show relationship between views and engagement
        st.subheader("Views vs Engagement")
        fig = px.scatter(page_stats, x="total_views", y="avg_views_per_session",
                         hover_name="pageTitle", trendline="ols",
                         title="Total Views vs Views Per Session")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("All Page Metrics")
        st.dataframe(page_stats.sort_values("total_views", ascending=False))
    
    # 3. Time-Based Analysis (if date available)
    if "date" in available_cols:
        st.header("⏱ Time-Based Patterns")
        
        # Convert date to datetime if not already
        page_views_data["date"] = pd.to_datetime(page_views_data["date"])
        
        # Weekly patterns
        page_views_data["week"] = page_views_data["date"].dt.to_period("W").astype(str)
        weekly_views = page_views_data.groupby("week")["screenPageViews"].sum().reset_index()
        
        # Calculate week-over-week growth
        weekly_views["wow_growth"] = weekly_views["screenPageViews"].pct_change() * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekly Page View Trends")
            fig = px.line(weekly_views, x="week", y="screenPageViews", 
                          title="Total Page Views by Week")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Week-over-Week Growth")
            fig = px.bar(weekly_views, x="week", y="wow_growth", 
                          title="Weekly Growth Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Daily patterns
        page_views_data["day_of_week"] = page_views_data["date"].dt.day_name()
        daily_pattern = page_views_data.groupby("day_of_week")["screenPageViews"].sum().reset_index()
        
        # Order days properly
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_pattern["day_of_week"] = pd.Categorical(daily_pattern["day_of_week"], categories=day_order, ordered=True)
        daily_pattern = daily_pattern.sort_values("day_of_week")
        
        st.subheader("Page Views by Day of Week")
        fig = px.bar(daily_pattern, x="day_of_week", y="screenPageViews",
                     title="Page View Distribution by Weekday")
        st.plotly_chart(fig, use_container_width=True)
        
        # 4. Page Trajectory Analysis
        st.header("📈 Page Performance Trajectories")
        
        # Get top 5 pages by total views
        top_5_pages = page_stats.sort_values("total_views", ascending=False).head(5)["pageTitle"].tolist()
        
        # Filter data for top pages
        top_pages_data = page_views_data[page_views_data["pageTitle"].isin(top_5_pages)]
        
        # Calculate cumulative views
        top_pages_data = top_pages_data.sort_values("date")
        top_pages_data["cumulative_views"] = top_pages_data.groupby("pageTitle")["screenPageViews"].cumsum()
        
        # Plot cumulative growth
        st.subheader("Cumulative Views Growth - Top 5 Pages")
        fig = px.line(top_pages_data, x="date", y="cumulative_views", color="pageTitle",
                      title="Cumulative Page Views Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # Plot daily views for top pages
        st.subheader("Daily Views - Top 5 Pages")
        fig = px.line(top_pages_data, x="date", y="screenPageViews", color="pageTitle",
                      title="Daily Page Views for Top Performing Pages")
        st.plotly_chart(fig, use_container_width=True)
    
    # 5. Page Path Analysis (if available)
    if "pagePath" in available_cols:
        st.header("🌐 Page Path Analysis")
        
        # Extract section from path (e.g., /blog/ -> blog)
        page_views_data["section"] = page_views_data["pagePath"].str.split("/").str[1].fillna("home")
        
        # Group by section
        section_stats = page_views_data.groupby("section").agg({
            "screenPageViews": "sum",
            "screenPageViewsPerSession": "mean"
        }).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Views by Website Section")
            fig = px.pie(section_stats, values="screenPageViews", names="section",
                         title="Page View Distribution by Website Section")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Engagement by Section")
            fig = px.bar(section_stats.sort_values("screenPageViewsPerSession", ascending=False),
                         x="section", y="screenPageViewsPerSession",
                         title="Average Views Per Session by Section")
            st.plotly_chart(fig, use_container_width=True)
    
    # 6. Page Performance Clustering
    st.header("🔍 Page Performance Segmentation")
    
    # Create performance segments
    if "total_views" in page_stats.columns and "avg_views_per_session" in page_stats.columns:
        # Normalize metrics for clustering
        page_stats["views_percentile"] = page_stats["total_views"].rank(pct=True) * 100
        page_stats["engagement_percentile"] = page_stats["avg_views_per_session"].rank(pct=True) * 100
        
        # Create segments
        conditions = [
            (page_stats["views_percentile"] >= 75) & (page_stats["engagement_percentile"] >= 75),
            (page_stats["views_percentile"] >= 75) & (page_stats["engagement_percentile"] < 75),
            (page_stats["views_percentile"] < 75) & (page_stats["engagement_percentile"] >= 75),
            (page_stats["views_percentile"] < 75) & (page_stats["engagement_percentile"] < 75)
        ]
        segments = ["High Views & Engagement", "High Views", "High Engagement", "Low Performance"]
        page_stats["segment"] = np.select(conditions, segments, default="Other")
        
        # Visualize segments
        st.subheader("Page Performance Matrix")
        fig = px.scatter(page_stats, x="views_percentile", y="engagement_percentile",
                         color="segment", hover_name="pageTitle",
                         title="Page Performance Segmentation\n(X: Views Percentile, Y: Engagement Percentile)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Show segment statistics
        st.subheader("Segment Breakdown")
        segment_stats = page_stats.groupby("segment").agg({
            "pageTitle": "count",
            "total_views": "sum",
            "avg_views_per_session": "mean"
        }).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("Number of Pages by Segment")
            fig = px.pie(segment_stats, values="pageTitle", names="segment",
                         title="Page Count by Segment")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.write("Traffic Share by Segment")
            fig = px.pie(segment_stats, values="total_views", names="segment",
                         title="Traffic Distribution by Segment")
            st.plotly_chart(fig, use_container_width=True)

# Page 4: Demographics
def page_demographics(demographics_data):
    st.title("👥 User Demographics & Acquisition")
    st.markdown("This page shows user demographics and acquisition patterns.")
    
    if demographics_data is None or demographics_data.empty:
        st.warning("No demographics data available.")
        return

    # Check which columns exist
    available_cols = demographics_data.columns.tolist()
    
    # 1. Geographic Analysis
    st.header("🌍 Geographic Distribution")
    
    if "country" in available_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Countries by Active Users")
            country_data = demographics_data.groupby("country")["activeUsers"].sum().nlargest(10).reset_index()
            fig = px.bar(country_data, x="country", y="activeUsers", 
                         color="activeUsers", title="Top 10 Countries")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("User Distribution by Country")
            country_total = demographics_data.groupby("country")["activeUsers"].sum().reset_index()
            fig = px.choropleth(
                country_total,
                locations="country",
                locationmode="country names",
                color="activeUsers",
                hover_name="country",
                title="Global User Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        if "city" in available_cols:
            st.subheader("Top Cities by Active Users")
            city_data = demographics_data.groupby(["country", "city"])["activeUsers"].sum().nlargest(15).reset_index()
            city_data["location"] = city_data["city"] + ", " + city_data["country"]
            fig = px.bar(city_data, x="location", y="activeUsers", 
                         title="Top 15 Cities", color="activeUsers")
            st.plotly_chart(fig, use_container_width=True)
    
    # 2. Acquisition Analysis
    st.header("📈 Acquisition Channels")
    
    if "firstUserSourceMedium" in available_cols:
        # Extract source and medium if in format "source / medium"
        if demographics_data["firstUserSourceMedium"].str.contains("/").any():
            demographics_data[["source", "medium"]] = demographics_data["firstUserSourceMedium"].str.split("/", expand=True)
            demographics_data["source"] = demographics_data["source"].str.strip()
            demographics_data["medium"] = demographics_data["medium"].str.strip()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top Traffic Sources")
                source_data = demographics_data.groupby("source")["activeUsers"].sum().nlargest(10).reset_index()
                fig = px.pie(source_data, values="activeUsers", names="source", 
                             title="User Acquisition by Source")
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("Acquisition Mediums")
                medium_data = demographics_data.groupby("medium")["activeUsers"].sum().reset_index()
                fig = px.bar(medium_data, x="medium", y="activeUsers", 
                             color="activeUsers", title="User Acquisition by Medium")
                st.plotly_chart(fig, use_container_width=True)
                
            # Time-based acquisition trends
            if "date" in available_cols:
                st.subheader("Acquisition Trends Over Time")
                time_data = demographics_data.groupby(["date", "source"])["activeUsers"].sum().reset_index()
                fig = px.line(time_data, x="date", y="activeUsers", color="source",
                              title="Daily User Acquisition by Source")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader("Acquisition Channels")
            source_data = demographics_data.groupby("firstUserSourceMedium")["activeUsers"].sum().nlargest(15).reset_index()
            fig = px.bar(source_data, x="firstUserSourceMedium", y="activeUsers",
                         title="Top 15 Acquisition Channels", color="activeUsers")
            st.plotly_chart(fig, use_container_width=True)
    
    # 3. Time-Based Analysis
    st.header("⏱ Time-Based Patterns")
    
    if "date" in available_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Daily Active Users")
            daily_users = demographics_data.groupby("date")["activeUsers"].sum().reset_index()
            fig = px.line(daily_users, x="date", y="activeUsers", 
                          title="Daily Active Users Trend")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Weekly Pattern")
            demographics_data["day_of_week"] = pd.to_datetime(demographics_data["date"]).dt.day_name()
            weekly_pattern = demographics_data.groupby("day_of_week")["activeUsers"].sum().reset_index()
            fig = px.bar(weekly_pattern, x="day_of_week", y="activeUsers",
                         category_orders={"day_of_week": ["Monday", "Tuesday", "Wednesday", 
                                                         "Thursday", "Friday", "Saturday", "Sunday"]},
                         title="Active Users by Day of Week")
            st.plotly_chart(fig, use_container_width=True)
    
    # 4. Combined Geographic-Acquisition Analysis
    if all(col in available_cols for col in ["country", "firstUserSourceMedium"]):
        st.header("🌐 Geographic Acquisition Patterns")
        
        # Top sources by country
        country_source = demographics_data.groupby(["country", "firstUserSourceMedium"])["activeUsers"].sum().reset_index()
        top_country_source = country_source.loc[country_source.groupby("country")["activeUsers"].idxmax()]
        
        fig = px.bar(top_country_source, x="country", y="activeUsers", color="firstUserSourceMedium",
                     title="Dominant Acquisition Channel by Country")
        st.plotly_chart(fig, use_container_width=True)

# Page 5: Device & Technology
def page_device_technology(device_data):
    st.title("📱 Device & Technology")
    st.markdown("This page shows the breakdown of users by device and technology.")
    
    if device_data is None or device_data.empty:
        st.warning("No device & technology data available.")
        return
    
    # Check available columns
    available_cols = device_data.columns.tolist()
    # st.write("Available columns in device data:", available_cols)  # Debug output
    
    # Determine which metric column to use (fallback to first numeric column if activeUsers not found)
    metric_col = "activeUsers" if "activeUsers" in available_cols else None
    if not metric_col:
        numeric_cols = device_data.select_dtypes(include=['number']).columns
        metric_col = numeric_cols[0] if len(numeric_cols) > 0 else None
    
    if not metric_col:
        st.error("No numeric columns found for analysis")
        return
    
    st.subheader(f"User Distribution by {metric_col}")
    
    # 1. Device Category Analysis
    if "deviceCategory" in available_cols:
        st.subheader("By Device Category")
        col1, col2 = st.columns(2)
        
        with col1:
            device_category_data = device_data.groupby("deviceCategory")[metric_col].sum().reset_index()
            fig = px.pie(device_category_data, values=metric_col, names="deviceCategory", 
                         title=f"{metric_col} by Device Category")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.bar(device_category_data, x="deviceCategory", y=metric_col,
                         color="deviceCategory", title=f"{metric_col} by Device Category")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Device category data not available")
    
    # 2. Operating System Analysis
    if "operatingSystem" in available_cols:
        st.subheader("By Operating System")
        os_data = device_data.groupby("operatingSystem")[metric_col].sum().nlargest(10).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(os_data, x="operatingSystem", y=metric_col,
                         title=f"Top 10 OS by {metric_col}")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = px.pie(os_data, values=metric_col, names="operatingSystem",
                         title=f"{metric_col} Distribution by OS")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Operating system data not available")
    
    # 3. Browser Analysis
    if "browser" in available_cols:
        st.subheader("By Browser")
        browser_data = device_data.groupby("browser")[metric_col].sum().nlargest(10).reset_index()
        fig = px.bar(browser_data, x="browser", y=metric_col, color="browser",
                     title=f"Top 10 Browsers by {metric_col}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Browser data not available")
    
    # 4. Combined Technology Analysis
    if all(col in available_cols for col in ["operatingSystem", "browser"]):
        st.subheader("OS & Browser Combinations")
        combo_data = device_data.groupby(["operatingSystem", "browser"])[metric_col].sum().nlargest(15).reset_index()
        combo_data["combo"] = combo_data["operatingSystem"] + " + " + combo_data["browser"]
        fig = px.bar(combo_data, x="combo", y=metric_col, color="operatingSystem",
                     title=f"Top 15 OS+Browser Combos by {metric_col}")
        st.plotly_chart(fig, use_container_width=True)
    
    # 5. Time Trends (if date column exists)
    if "date" in available_cols:
        st.subheader("Technology Trends Over Time")
        time_data = device_data.groupby(["date", "deviceCategory"])[metric_col].sum().reset_index()
        fig = px.line(time_data, x="date", y=metric_col, color="deviceCategory",
                      title=f"{metric_col} Trends by Device Category")
        st.plotly_chart(fig, use_container_width=True)

# Page 6: Events
def page_events(events_data):
    st.title("🎯 User Events Analysis")
    st.markdown("This page provides comprehensive insights into user events and interactions.")
    
    if events_data is None or events_data.empty:
        st.warning("No events data available.")
        return

    # Check available columns
    available_cols = events_data.columns.tolist()
    
    # 1. Event Overview Metrics
    st.header("📊 Event Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_events = events_data["eventCount"].sum()
        display_metric("Total Events Recorded", f"{total_events:,}", 0)
    
    with col2:
        unique_events = events_data["eventName"].nunique()
        display_metric("Unique Event Types", unique_events, 0)
    
    with col3:
        avg_per_event = total_events / unique_events if unique_events > 0 else 0
        display_metric("Avg. Triggers per Event", f"{avg_per_event:,.1f}", 0)

    # 2. Main Event Visualization
    st.header("📈 Event Distribution")
    
    # Group by event name and calculate percentages
    event_count_data = events_data.groupby("eventName")["eventCount"].sum().reset_index()
    event_count_data["percentage"] = (event_count_data["eventCount"] / total_events) * 100
    
    tab1, tab2, tab3 = st.tabs(["Bar Chart", "Pie Chart", "Data Table"])
    
    with tab1:
        fig = px.bar(event_count_data.sort_values("eventCount", ascending=False), 
                    x="eventName", y="eventCount", 
                    color="eventCount",
                    title="Event Count by Event Name",
                    labels={"eventCount": "Total Triggers", "eventName": "Event Name"})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.pie(event_count_data, values="eventCount", names="eventName",
                    title="Event Distribution by Percentage",
                    hover_data=["percentage"])
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.dataframe(event_count_data.sort_values("eventCount", ascending=False))
    
    # 3. Time-Based Analysis (if date column exists)
    if "date" in available_cols:
        st.header("⏱ Event Trends Over Time")
        
        # Convert date to datetime if it's not already
        events_data["date"] = pd.to_datetime(events_data["date"])
        
        # Calculate week-over-week change for delta values
        events_data["week"] = events_data["date"].dt.to_period('W')
        weekly_events = events_data.groupby("week")["eventCount"].sum().reset_index()
        weekly_events["pct_change"] = weekly_events["eventCount"].pct_change() * 100
        
        # Get the latest week's data safely
        current_week_data = weekly_events.iloc[-1] if len(weekly_events) > 0 else None
        
        # Daily event trends
        daily_events = events_data.groupby("date")["eventCount"].sum().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Safely handle current_week_data
            if current_week_data is not None:
                delta_value = current_week_data["pct_change"]
                current_week_count = current_week_data["eventCount"]
            else:
                delta_value = 0
                current_week_count = "N/A"
            
            display_metric("Weekly Event Volume", 
                         f"{current_week_count:,}" if current_week_data is not None else "N/A", 
                         delta_value)
            
            fig = px.line(daily_events, x="date", y="eventCount",
                         title="Daily Event Volume Trend")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Weekly pattern
            events_data["day_of_week"] = events_data["date"].dt.day_name()
            weekly_pattern = events_data.groupby("day_of_week")["eventCount"].sum().reset_index()
            
            # Calculate day-over-day change
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekly_pattern = weekly_pattern.set_index("day_of_week").loc[day_order].reset_index()
            weekly_pattern["pct_change"] = weekly_pattern["eventCount"].pct_change() * 100
            
            fig = px.bar(weekly_pattern, x="day_of_week", y="eventCount",
                         category_orders={"day_of_week": day_order},
                         title="Events by Day of Week")
            st.plotly_chart(fig, use_container_width=True)
        
        # Top events over time with deltas
        st.subheader("Top Events Over Time")
        top_events_over_time = events_data.groupby(["date", "eventName"])["eventCount"].sum().reset_index()
        top_5_events = event_count_data.nlargest(5, "eventCount")["eventName"].tolist()
        filtered_events = top_events_over_time[top_events_over_time["eventName"].isin(top_5_events)]
        
        # Calculate deltas for top events
        event_deltas = []
        for event in top_5_events:
            event_data = filtered_events[filtered_events["eventName"] == event]
            if len(event_data) > 1:
                delta = (event_data.iloc[-1]["eventCount"] - event_data.iloc[-2]["eventCount"]) / event_data.iloc[-2]["eventCount"] * 100
            else:
                delta = 0
            event_deltas.append(delta)
        
        # Display top events metrics
        cols = st.columns(len(top_5_events))
        for i, (event, delta) in enumerate(zip(top_5_events, event_deltas)):
            event_count = event_count_data[event_count_data["eventName"] == event]["eventCount"].values[0]
            with cols[i]:
                display_metric(f"{event}", f"{event_count:,}", delta)
        
        fig = px.line(filtered_events, x="date", y="eventCount", color="eventName",
                     title="Trend of Top 5 Events Over Time")
        st.plotly_chart(fig, use_container_width=True)


# Page 7: E-commerce
def page_ecommerce(ecommerce_data):
    st.title("🛒 E-commerce")
    st.markdown("This page shows the performance of e-commerce products.")

    if ecommerce_data is not None and not ecommerce_data.empty:
        # Group by product name
        st.subheader("Revenue by Product")
        product_revenue_data = ecommerce_data.groupby("productName")["itemRevenue"].sum().reset_index()
        fig = px.bar(product_revenue_data, x="productName", y="itemRevenue", title="Revenue by Product")
        st.plotly_chart(fig, use_container_width=True)

        # Group by product category
        st.subheader("Items Purchased by Product Category")
        category_data = ecommerce_data.groupby("productCategory")["itemsPurchased"].sum().reset_index()
        fig = px.pie(category_data, values="itemsPurchased", names="productCategory", title="Items Purchased by Product Category")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No e-commerce data available.")

# Page 8: User Lifetime Value (LTV)
def page_ltv(ltv_data=None):
    st.title("💰 Customer Lifetime Value Analysis")
    
    # Check if we have direct LTV data
    if ltv_data is not None and not ltv_data.empty:
        return analyze_ltv_data(ltv_data)
    
    # If no LTV data, try to derive from session state
    st.warning("No direct LTV data available. Attempting to derive from available data...")
    
    # Try to get required data from session state
    acquisition_data = st.session_state.get('acquisition_data')
    conversion_data = st.session_state.get('conversion_data')
    
    if acquisition_data is not None and conversion_data is not None:
        derived_ltv = derive_ltv_from_available_data(acquisition_data, conversion_data)
        if derived_ltv is not None:
            return analyze_derived_ltv(derived_ltv)
    
    # If we get here, no data was available
    show_ltv_help_instructions()
    show_sample_ltv_analysis()

def show_ltv_help_instructions():
    st.error("""
    Unable to calculate LTV. You need one of these data sources:
    
    1. **Direct LTV Data** (preferred):
       - Worksheet named "LTV" with columns:
         - `user_id`, `user_lifetime_revenue`, `user_lifetime_transactions`, `date`
    
    2. **Derived from Analytics**:
       - Acquisition data (userId, firstUserSource, date)
       - Conversion data (userId, purchaseRevenue, transactions)
    """)
    
    st.markdown("""
    ### How to enable LTV tracking:
    1. **For direct LTV**:
       - Create an "LTV" worksheet in your Google Sheet
       - Include user revenue and transaction history
    
    2. **For derived LTV**:
       - Ensure your GA4 data includes:
         - User IDs (enable userId tracking)
         - Purchase revenue data
         - Acquisition sources
    """)

def show_sample_ltv_analysis():
    if st.checkbox("Show sample LTV analysis for demonstration"):
        st.info("Displaying sample data for demonstration purposes")
        
        # Generate sample data
        sample_size = 1000
        np.random.seed(42)
        
        sample_ltv = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(sample_size)],
            'user_lifetime_revenue': np.random.lognormal(3, 1, sample_size).round(2),
            'user_lifetime_transactions': np.random.poisson(3, sample_size),
            'date': pd.date_range('2025-02-10', periods=sample_size).strftime('%Y-%m-%d'),
            'acquisition_source': np.random.choice(['google', 'facebook', 'direct', 'organic'], sample_size),
            'acquisition_medium': np.random.choice(['cpc', 'organic', 'referral', 'email'], sample_size)
        })
        
        # Create buckets
        conditions = [
            (sample_ltv['user_lifetime_revenue'] > 100),
            (sample_ltv['user_lifetime_revenue'] > 50),
            (sample_ltv['user_lifetime_revenue'] > 0),
            (sample_ltv['user_lifetime_revenue'] == 0)
        ]
        choices = ['high', 'medium', 'low', 'none']
        sample_ltv['ltv_bucket'] = np.select(conditions, choices, default='none')
        
        analyze_ltv_data(sample_ltv)

def derive_ltv_from_available_data(acquisition_data, conversion_data):
    """Create LTV metrics from available GA4 data"""
    try:
        # Check for required columns
        required_acq = ['userId', 'firstUserSource', 'firstUserMedium', 'date']
        required_conv = ['userId', 'purchaseRevenue', 'transactions']
        
        if not all(col in acquisition_data.columns for col in required_acq):
            st.warning("Acquisition data missing required columns")
            return None
            
        if not all(col in conversion_data.columns for col in required_conv):
            st.warning("Conversion data missing required columns")
            return None
        
        # Merge and calculate
        ltv_data = pd.merge(
            acquisition_data[required_acq],
            conversion_data.groupby('userId')[required_conv[1:]].sum().reset_index(),
            on='userId',
            how='left'
        ).fillna(0)
        
        # Rename columns to standard format
        ltv_data = ltv_data.rename(columns={
            'userId': 'user_id',
            'purchaseRevenue': 'user_lifetime_revenue',
            'transactions': 'user_lifetime_transactions',
            'firstUserSource': 'acquisition_source',
            'firstUserMedium': 'acquisition_medium'
        })
        
        return ltv_data
        
    except Exception as e:
        st.error(f"Error deriving LTV: {str(e)}")
        return None

def analyze_ltv_data(ltv_data):
    """Main analysis function for LTV data"""
    st.success("LTV data loaded successfully!")
    
    # Standardize column names
    ltv_data.columns = ltv_data.columns.str.lower().str.replace(' ', '_')
    
    # 1. Key Metrics
    st.header("📊 Key Metrics")
    cols = st.columns(4)
    metrics = [
        ('Average LTV', 'user_lifetime_revenue', 'mean', '${:,.2f}'),
        ('Median LTV', 'user_lifetime_revenue', 'median', '${:,.2f}'),
        ('Paying Users', 'user_lifetime_revenue', lambda x: (x > 0).mean() * 100, '{:.1f}%'),
        ('Avg Transactions', 'user_lifetime_transactions', 'mean', '{:.1f}')
    ]
    
    for col, (label, col_name, agg_func, fmt) in zip(cols, metrics):
        if col_name in ltv_data.columns:
            value = ltv_data[col_name].agg(agg_func)
            col.metric(label, fmt.format(value))
    
    # 2. Distribution Analysis
    st.header("📈 Distribution Analysis")
    if 'user_lifetime_revenue' in ltv_data.columns:
        fig = px.histogram(ltv_data, x='user_lifetime_revenue', nbins=50,
                          title='LTV Value Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # 3. Cohort Analysis
    if 'date' in ltv_data.columns:
        st.header("🕰️ Cohort Analysis")
        ltv_data['cohort'] = pd.to_datetime(ltv_data['date']).dt.to_period('M')
        cohort_data = ltv_data.groupby('cohort').agg({
            'user_lifetime_revenue': ['mean', 'median', 'count'],
            'user_id': 'nunique'
        }).reset_index()
        
        # Flatten multi-index columns
        cohort_data.columns = ['_'.join(col).strip() if col[1] else col[0] 
                             for col in cohort_data.columns.values]
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(cohort_data, x='cohort', y='user_lifetime_revenue_mean',
                         title='Average LTV by Cohort')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(cohort_data, x='cohort', y='user_id_nunique',
                        title='Users by Cohort')
            st.plotly_chart(fig, use_container_width=True)
    
    # 4. Acquisition Analysis
    if all(col in ltv_data.columns for col in ['acquisition_source', 'user_lifetime_revenue']):
        st.header("📡 Acquisition Performance")
        source_data = ltv_data.groupby('acquisition_source').agg({
            'user_lifetime_revenue': ['mean', 'count'],
            'user_lifetime_transactions': 'mean'
        }).reset_index()
        
        source_data.columns = ['source', 'avg_ltv', 'users', 'avg_transactions']
        
        tab1, tab2 = st.tabs(["By LTV", "By Volume"])
        with tab1:
            fig = px.bar(source_data.sort_values('avg_ltv', ascending=False),
                        x='source', y='avg_ltv',
                        title='Average LTV by Acquisition Source')
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.pie(source_data, values='users', names='source',
                        title='User Acquisition Distribution')
            st.plotly_chart(fig, use_container_width=True)

# Page 9: Audience & Segments
def page_audience(audience_data):
    st.title("👥 Audience & Segments")
    
    # Handle empty data case more gracefully
    if audience_data is None or audience_data.empty:
        st.warning("""
        No audience data available. This could be because:
        - The worksheet is missing from your Google Sheet
        - The worksheet is empty
        - Required columns are missing
        """)
        
        st.subheader("Expected Data Format")
        st.dataframe(pd.DataFrame({
            'audienceName': ['Returning Visitors', 'Mobile Users'],
            'activeUsers': [1500, 800],
            'conversions': [150, 80]
        }))
        return
    
    # Ensure we have required columns
    required_cols = ['audienceName', 'activeUsers']
    missing_cols = [col for col in required_cols if col not in audience_data.columns]
    
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return
    
    # Main analysis
    st.header("Audience Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Audiences", audience_data['audienceName'].nunique())
    
    with col2:
        st.metric("Total Active Users", audience_data['activeUsers'].sum())
    
    st.subheader("Top Audiences by Active Users")
    top_audiences = audience_data.sort_values('activeUsers', ascending=False).head(10)
    fig = px.bar(top_audiences, x='audienceName', y='activeUsers')
    st.plotly_chart(fig, use_container_width=True)
    
    if 'conversions' in audience_data.columns:
        st.subheader("Conversion Rates")
        audience_data['conversion_rate'] = (audience_data['conversions'] / audience_data['activeUsers']) * 100
        fig = px.bar(audience_data.sort_values('conversion_rate', ascending=False),
                    x='audienceName', y='conversion_rate',
                    labels={'conversion_rate': 'Conversion Rate (%)'})
        st.plotly_chart(fig, use_container_width=True)

# Page 10: App-Specific Data
def page_app(app_data):
    st.title("📱 App-Specific Data")
    st.markdown("This page shows the performance of your app.")

    if app_data is not None and not app_data.empty:
        # Check if 'screenPageViews' column exists
        if "screenPageViews" in app_data.columns:
            # Group by app version
            st.subheader("Screen Views by App Version")
            app_version_data = app_data.groupby("appVersion")["screenPageViews"].sum().reset_index()
            fig = px.bar(app_version_data, x="appVersion", y="screenPageViews", title="Screen Views by App Version")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("The 'screenPageViews' column is missing in the app data.")

        # Group by platform
        st.subheader("User Engagement by Platform")
        platform_data = app_data.groupby("platform")["userEngagementDuration"].sum().reset_index()
        fig = px.pie(platform_data, values="userEngagementDuration", names="platform", title="User Engagement by Platform")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No app-specific data available.")

# Page 11: Funnel Analysis
def page_funnel(funnel_data):
    st.title("📊 Funnel Analysis")
    st.markdown("This page shows the performance of your conversion funnel.")

    if funnel_data is not None and not funnel_data.empty:
        # Group by funnel step
        st.subheader("Conversions by Funnel Step")
        funnel_conversions_data = funnel_data.groupby("funnelStep")["funnelConversions"].sum().reset_index()
        fig = px.bar(funnel_conversions_data, x="funnelStep", y="funnelConversions", title="Conversions by Funnel Step")
        st.plotly_chart(fig, use_container_width=True)

        # Group by funnel drop-off rate
        st.subheader("Drop-Off Rate by Funnel Step")
        funnel_dropoff_data = funnel_data.groupby("funnelStep")["funnelDropOffRate"].mean().reset_index()
        fig = px.line(funnel_dropoff_data, x="funnelStep", y="funnelDropOffRate", title="Drop-Off Rate by Funnel Step")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No funnel analysis data available.")

# Page 12: Retention & Cohorts
def page_retention(retention_data):
    st.title("📈 Retention & Cohorts")
    st.markdown("This page shows user retention and cohort analysis.")

    if retention_data is not None and not retention_data.empty:
        # Group by cohort
        st.subheader("Retained Users by Cohort")
        cohort_data = retention_data.groupby("cohort")["retainedUsers"].sum().reset_index()
        fig = px.bar(cohort_data, x="cohort", y="retainedUsers", title="Retained Users by Cohort")
        st.plotly_chart(fig, use_container_width=True)

        # Group by retention rate
        st.subheader("Retention Rate by Cohort")
        retention_rate_data = retention_data.groupby("cohort")["retentionRate"].mean().reset_index()
        fig = px.line(retention_rate_data, x="cohort", y="retentionRate", title="Retention Rate by Cohort")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No retention & cohorts data available.")

# Page 13: Site Speed & Performance
def page_site_speed(site_speed_data):
    st.title("⏱️ Site Speed & Performance")
    st.markdown("This page shows the performance of your website.")

    if site_speed_data is not None and not site_speed_data.empty:
        # Check if 'eventName' column exists
        if "eventName" in site_speed_data.columns:
            # Filter for the custom event 'page_load'
            page_load_data = site_speed_data[site_speed_data["eventName"] == "page_load"]

            if not page_load_data.empty:
                # Group by page path and calculate average page load time
                st.subheader("Average Page Load Time by Page")
                load_time_data = page_load_data.groupby("pagePath")["averageSessionDuration"].mean().reset_index()
                fig = px.bar(load_time_data, x="pagePath", y="averageSessionDuration", title="Average Page Load Time by Page")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No page load time data available.")
        else:
            # If 'eventName' is missing, display general site speed data
            st.subheader("Average Session Duration by Page")
            load_time_data = site_speed_data.groupby("pagePath")["averageSessionDuration"].mean().reset_index()
            fig = px.bar(load_time_data, x="pagePath", y="averageSessionDuration", title="Average Session Duration by Page")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No site speed & performance data available.")



# Page 14: Error Tracking
def page_error_tracking(error_data):
    st.title("❌ Error Tracking")
    st.markdown("This page shows errors encountered by users.")

    if error_data is not None and not error_data.empty:
        # Group by error type
        st.subheader("Error Count by Error Type")
        error_count_data = error_data.groupby("eventName")["eventCount"].sum().reset_index()
        fig = px.bar(error_count_data, x="eventName", y="eventCount", title="Error Count by Error Type")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No error tracking data available.")


# Page 15: Deepseek AI Insights with Digital Marketing Expert
def page_deepseek_ai(user_traffic_data, conversion_data, demographics_data, device_data, events_data, ecommerce_data, ltv_data, audience_data, app_data, funnel_data, retention_data, site_speed_data, error_data):
    st.title("🤖 AI Insights")
    st.markdown("This page provides advanced insights and recommendations using AI as your Digital Marketing Expert.")

    # Deepseek API endpoint and headers (global scope)
    DEEPSEEK_API_URL = "https://api.deepseek.ai/v1/chat"  # Replace with actual endpoint
    headers = {
        "Authorization": f"Bearer <YOUR API KEY>",  # Replace with your API key
        "Content-Type": "application/json"
    }

    # Chatbot Interface
    st.subheader("Digital Marketing Expert Chatbot")
    st.markdown("Ask the chatbot for insights, predictions, and recommendations.")

    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # User input
    user_input = st.text_input("Ask me anything about your digital marketing data:")

    if user_input:
        # Prepare all available data for Deepseek AI
        data_to_send = {
            "query": user_input,
            "data": {}
        }

        # Function to convert Timestamp columns to strings
        def convert_timestamps(df):
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].astype(str)  # Convert Timestamp to string
            return df

        # Add available datasets to the payload
        if user_traffic_data is not None:
            user_traffic_data = convert_timestamps(user_traffic_data)
            data_to_send["data"]["user_traffic"] = user_traffic_data.to_dict(orient="records")
        if conversion_data is not None:
            conversion_data = convert_timestamps(conversion_data)
            data_to_send["data"]["conversions"] = conversion_data.to_dict(orient="records")
        if demographics_data is not None:
            demographics_data = convert_timestamps(demographics_data)
            data_to_send["data"]["demographics"] = demographics_data.to_dict(orient="records")
        if device_data is not None:
            device_data = convert_timestamps(device_data)
            data_to_send["data"]["device"] = device_data.to_dict(orient="records")
        if events_data is not None:
            events_data = convert_timestamps(events_data)
            data_to_send["data"]["events"] = events_data.to_dict(orient="records")
        if ecommerce_data is not None:
            ecommerce_data = convert_timestamps(ecommerce_data)
            data_to_send["data"]["ecommerce"] = ecommerce_data.to_dict(orient="records")
        if ltv_data is not None:
            ltv_data = convert_timestamps(ltv_data)
            data_to_send["data"]["ltv"] = ltv_data.to_dict(orient="records")
        if audience_data is not None:
            audience_data = convert_timestamps(audience_data)
            data_to_send["data"]["audience"] = audience_data.to_dict(orient="records")
        if app_data is not None:
            app_data = convert_timestamps(app_data)
            data_to_send["data"]["app"] = app_data.to_dict(orient="records")
        if funnel_data is not None:
            funnel_data = convert_timestamps(funnel_data)
            data_to_send["data"]["funnel"] = funnel_data.to_dict(orient="records")
        if retention_data is not None:
            retention_data = convert_timestamps(retention_data)
            data_to_send["data"]["retention"] = retention_data.to_dict(orient="records")
        if site_speed_data is not None:
            site_speed_data = convert_timestamps(site_speed_data)
            data_to_send["data"]["site_speed"] = site_speed_data.to_dict(orient="records")
        if error_data is not None:
            error_data = convert_timestamps(error_data)
            data_to_send["data"]["errors"] = error_data.to_dict(orient="records")

        # Send user query and data to Deepseek AI
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data_to_send, timeout=10)  # Add timeout
            if response.status_code == 200:
                chatbot_response = response.json().get("response", "No response from Deepseek AI.")
                st.session_state.chat_history.append({"user": user_input, "bot": chatbot_response})
            else:
                st.error(f"Failed to get response from Deepseek AI. Status Code: {response.status_code}")
                # Fallback: Use predefined insights
                chatbot_response = "Deepseek AI is currently unavailable. Here are some general insights based on your data: [Placeholder Insights]"
                st.session_state.chat_history.append({"user": user_input, "bot": chatbot_response})
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to Deepseek AI. Please check your internet connection or the API endpoint. Error: {e}")
            # Fallback: Use predefined insights
            chatbot_response = "Deepseek AI is currently unavailable. Here are some general insights based on your data: [Placeholder Insights]"
            st.session_state.chat_history.append({"user": user_input, "bot": chatbot_response})

    # Display chat history
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**Bot:** {chat['bot']}")
        st.markdown("---")

    # Insights and Prescriptions Section
    st.subheader("Automated Insights and Prescriptions")
    if st.button("Generate Insights and Prescriptions"):
        # Prepare all available data for Deepseek AI
        data_to_send = {
            "query": "Analyze the provided data and provide insights and prescriptions for future digital marketing goals.",
            "data": {}
        }

        # Function to convert Timestamp columns to strings
        def convert_timestamps(df):
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].astype(str)  # Convert Timestamp to string
            return df

        # Add available datasets to the payload
        if user_traffic_data is not None:
            user_traffic_data = convert_timestamps(user_traffic_data)
            data_to_send["data"]["user_traffic"] = user_traffic_data.to_dict(orient="records")
        if conversion_data is not None:
            conversion_data = convert_timestamps(conversion_data)
            data_to_send["data"]["conversions"] = conversion_data.to_dict(orient="records")
        if demographics_data is not None:
            demographics_data = convert_timestamps(demographics_data)
            data_to_send["data"]["demographics"] = demographics_data.to_dict(orient="records")
        if device_data is not None:
            device_data = convert_timestamps(device_data)
            data_to_send["data"]["device"] = device_data.to_dict(orient="records")
        if events_data is not None:
            events_data = convert_timestamps(events_data)
            data_to_send["data"]["events"] = events_data.to_dict(orient="records")
        if ecommerce_data is not None:
            ecommerce_data = convert_timestamps(ecommerce_data)
            data_to_send["data"]["ecommerce"] = ecommerce_data.to_dict(orient="records")
        if ltv_data is not None:
            ltv_data = convert_timestamps(ltv_data)
            data_to_send["data"]["ltv"] = ltv_data.to_dict(orient="records")
        if audience_data is not None:
            audience_data = convert_timestamps(audience_data)
            data_to_send["data"]["audience"] = audience_data.to_dict(orient="records")
        if app_data is not None:
            app_data = convert_timestamps(app_data)
            data_to_send["data"]["app"] = app_data.to_dict(orient="records")
        if funnel_data is not None:
            funnel_data = convert_timestamps(funnel_data)
            data_to_send["data"]["funnel"] = funnel_data.to_dict(orient="records")
        if retention_data is not None:
            retention_data = convert_timestamps(retention_data)
            data_to_send["data"]["retention"] = retention_data.to_dict(orient="records")
        if site_speed_data is not None:
            site_speed_data = convert_timestamps(site_speed_data)
            data_to_send["data"]["site_speed"] = site_speed_data.to_dict(orient="records")
        if error_data is not None:
            error_data = convert_timestamps(error_data)
            data_to_send["data"]["errors"] = error_data.to_dict(orient="records")

        # Send data to Deepseek AI
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data_to_send, timeout=10)  # Add timeout
            if response.status_code == 200:
                insights = response.json().get("response", "No insights generated.")
                st.markdown(f"**Insights and Prescriptions:** {insights}")
            else:
                st.error(f"Failed to generate insights. Status Code: {response.status_code}")
                # Fallback: Use predefined insights
                st.markdown("**Insights and Prescriptions:** Deepseek AI is currently unavailable. Here are some general insights based on your data: [Placeholder Insights]")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to Deepseek AI. Please check your internet connection or the API endpoint. Error: {e}")
            # Fallback: Use predefined insights
            st.markdown("**Insights and Prescriptions:** Deepseek AI is currently unavailable. Here are some general insights based on your data: [Placeholder Insights]")

#Page 16: Function for keyword analysis
def page_search_console(search_console_data):
    st.title("🔍 Search Console Data")
    st.markdown("This page shows search performance data from Google Search Console.")

    if search_console_data is not None and not search_console_data.empty:
        # Display top queries
        st.subheader("Top Queries by Clicks")
        top_queries = search_console_data.sort_values(by="Clicks", ascending=False).head(10)
        st.dataframe(top_queries)

        # Display top pages
        st.subheader("Top Pages by Clicks")
        top_pages = search_console_data.groupby("Page")["Clicks"].sum().reset_index().sort_values(by="Clicks", ascending=False).head(10)
        st.dataframe(top_pages)
    else:
        st.warning("No search console data available.")

#Page17: SEO Metrics Overview
def page_seo_overview(search_console_data, ga4_data, seo_data):
    st.title("📊 SEO Metrics Overview")
    st.markdown("This page provides an overview of key SEO metrics.")

    if search_console_data is not None and not search_console_data.empty:
        st.header("Google Search Console Data")
        st.subheader("Top Queries by Clicks")
        top_queries = search_console_data.groupby('Query')['Clicks'].sum().reset_index().sort_values(by='Clicks', ascending=False).head(10)
        st.dataframe(top_queries)

        st.subheader("CTR by Device")
        ctr_by_device = search_console_data.groupby('Device')['CTR'].mean().reset_index()
        fig = px.bar(ctr_by_device, x='Device', y='CTR', title="CTR by Device")
        st.plotly_chart(fig, use_container_width=True)

    if ga4_data is not None and not ga4_data.empty:
        st.header("Google Analytics 4 Data")
        st.subheader("Sessions by Page")
        sessions_by_page = ga4_data.groupby('Page')['Sessions'].sum().reset_index().sort_values(by='Sessions', ascending=False).head(10)
        st.dataframe(sessions_by_page)

        st.subheader("Average Session Duration by Device")
        avg_duration_by_device = ga4_data.groupby('Device')['AvgSessionDuration'].mean().reset_index()
        fig = px.bar(avg_duration_by_device, x='Device', y='AvgSessionDuration', title="Average Session Duration by Device")
        st.plotly_chart(fig, use_container_width=True)

    if seo_data is not None and not seo_data.empty:
        st.header("Third-Party SEO Data")
        st.subheader("Backlinks and Domain Authority")
        st.dataframe(seo_data)

def page_smm_overview(facebook_data, instagram_data, linkedin_metrics, linkedin_posts, youtube_data, x_data):
    st.title("📊 Social Media Management Overview")
    st.markdown("This page provides a high-level overview of your social media performance.")

    # Facebook Metrics
    if facebook_data is not None and not facebook_data.empty:
        st.subheader("📘 Facebook Metrics")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            total_posts = facebook_data["Title"].count()
            display_metric("Total Posts", total_posts, 0)
        with col2:
            total_reach = facebook_data["Reach"].sum()
            display_metric("Total Reach", total_reach, 0)
        with col3:
            total_reach = facebook_data["Reach"].sum()
            display_metric("Total Reach", total_reach, 0)
        with col4:
            total_comments = facebook_data["Comments"].sum()
            display_metric("Total Comments", total_comments, 0)
        with col5:
            total_shares = facebook_data["Shares"].sum()
            display_metric("Total Shares", total_shares, 0)
        with col6:
            total_clicks = facebook_data["Total clicks"].sum()
            display_metric("Total Clicks", total_clicks, 0)

    # Instagram Metrics
    if instagram_data is not None and not instagram_data.empty:
        st.subheader("📸 Instagram Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_reactions = instagram_data["Reactions"].sum()
            display_metric("Total Reactions", total_reactions, 0)
        with col2:
            total_comments = instagram_data["Comments"].sum()
            display_metric("Total Comments", total_comments, 0)
        with col3:
            total_followers = instagram_data["Total clicks"].sum()
            display_metric("Total Followers", total_followers, 0)

    # LinkedIn Metrics
    st.subheader("🔗 LinkedIn Metrics")
    if linkedin_metrics is not None and not linkedin_metrics.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            total_impressions = linkedin_metrics['Impressions (total)'].sum()
            display_metric("Total Impressions", total_impressions,0)
        with col2:
            total_clicks = linkedin_metrics['Clicks (total)'].sum()
            display_metric("Total Clicks", total_clicks,0)
        with col3:
            total_engagement = linkedin_metrics['Engagement rate (total)'].mean()
            display_metric("Avg Engagement Rate", f"{total_engagement:.2f}%",0)
    
def page_facebook(facebook_data):
    st.title("📘 Facebook Metrics")
    st.markdown("This page provides detailed insights into Facebook performance.")

    if facebook_data is not None and not facebook_data.empty:
        # Ensure no missing values in "Engaged users" column
        facebook_data = facebook_data.fillna(0)
        st.subheader("🔹 Engagement Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            total_reach = facebook_data["Reach"].sum()
            display_metric("Total Reach", total_reach, 0)
        with col2:
            total_engagement = facebook_data["Reactions, comments and shares"].sum()  # Updated
            display_metric("Total Engagement", total_engagement, 0)
        with col3:
            total_comments = facebook_data["Comments"].sum()
            display_metric("Total Comments", total_comments, 0)
        with col4:
            total_shares = facebook_data["Shares"].sum()
            display_metric("Total Shares", total_shares, 0)
        with col5:
            total_clicks = facebook_data["Total clicks"].sum()
            display_metric("Total Clicks", total_clicks, 0)

        # Engagement Trends Over Time
        st.subheader("📊 Facebook Engagement Trends")
        facebook_data["Date"] = pd.to_datetime(facebook_data["Publish time"], errors='coerce').dt.date
        fb_trends = facebook_data.groupby("Date")[["Reactions, comments and shares", "Comments", "Shares"]].sum().reset_index()
        fig = px.line(fb_trends, x="Date", y=["Reactions, comments and shares", "Comments", "Shares"], title="Facebook Engagement Trends")
        st.plotly_chart(fig, use_container_width=True)

        # Top 5 Engaging Posts
        st.subheader("🔥 Top 5 Most Engaging Posts")
        top_posts = facebook_data.sort_values(by="Reactions, comments and shares", ascending=False).head(5)
        st.dataframe(top_posts[["Title", "Reactions, comments and shares", "Comments", "Shares", "Permalink"]])

        # Reach vs. Engagement
        st.subheader("📊 Reach vs. Engagement")
        fig = px.scatter(facebook_data, x="Reach", y="Reactions, comments and shares", size="Engaged users", title="Reach vs. Engagement Performance")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("💰 Revenue & User Experience Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_earnings = facebook_data["Estimated earnings (USD)"].sum()
            display_metric("Estimated Earnings (USD)", f"${total_earnings:.2f}", 0)
        with col2:
            negative_feedback = facebook_data["Negative feedback from users"].sum()
            display_metric("Negative Feedback", negative_feedback, 0)
        with col3:
            click_through_rate = (total_clicks / total_reach) * 100 if total_reach > 0 else 0
            display_metric("Click-Through Rate (CTR)", f"{click_through_rate:.2f}%", 0)

        # Engagement Trends Over Time
        st.subheader("📊 Facebook Engagement Trends")
        facebook_data["Date"] = pd.to_datetime(facebook_data["Publish time"], errors='coerce').dt.date
        fb_trends = facebook_data.groupby("Date")[["Reactions, comments and shares", "Comments", "Shares"]].sum().reset_index()

        fig1 = px.line(fb_trends, x="Date", y=["Reactions, comments and shares", "Comments", "Shares"], title="Facebook Engagement Trends")
        st.plotly_chart(fig1, use_container_width=True, key="facebook_trends")

        # Engagement Distribution Chart
        st.subheader("📊 Engagement Distribution")
        fig2 = px.histogram(facebook_data, x="Reactions, comments and shares", nbins=20, title="Engagement Distribution")
        st.plotly_chart(fig2, use_container_width=True, key="facebook_distribution")

        # Top 5 Performing Posts
        st.subheader("🔥 Top 5 Most Engaging Posts")
        top_posts = facebook_data.sort_values(by="Reactions, comments and shares", ascending=False).head(5)
        st.dataframe(top_posts[["Title", "Reactions, comments and shares", "Comments", "Shares", "Permalink"]])

        # Reach vs. Engagement (Scatter Plot)
        facebook_data["Engaged users"] = facebook_data["Engaged users"].fillna(0)
        scatter_data = facebook_data[["Reach", "Reactions, comments and shares", "Engaged users"]].dropna()
        
        fig3 = px.scatter(scatter_data, x="Reach", y="Reactions, comments and shares", size="Engaged users",
                          title="Reach vs. Engagement Performance")
        st.plotly_chart(fig3, use_container_width=True, key="facebook_scatter")
    else:
        st.warning("⚠️ No Facebook data available.")

def page_instagram(instagram_data):
    st.title("📸 Instagram Metrics")
    st.markdown("This page shows the performance metrics for Instagram.")

    if instagram_data is not None and not instagram_data.empty:
        st.subheader("Engagement Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_likes = instagram_data["Reactions"].sum()
            display_metric("Total Likes", total_likes, 0)
        with col2:
            total_comments = instagram_data["Comments"].sum()
            display_metric("Total Comments", total_comments, 0)
        with col3:
            total_followers = instagram_data["Total clicks"].sum()
            display_metric("Total Followers", total_followers, 0)

        st.subheader("Likes Over Time")
        fig = px.line(instagram_data, x="Date", y="Reach", title="Likes Over Time")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Comments Over Time")
        fig = px.line(instagram_data, x="Date", y="Comments", title="Comments Over Time")
        st.plotly_chart(fig, use_container_width=True)

# Function to display LinkedIn data in the dashboard
def page_linkedin_analysis(metrics_df, posts_df):
    """
    Display LinkedIn metrics and posts analysis in a single page.
    """
    st.title("🔗 LinkedIn Analysis")
    st.markdown("This page analyzes LinkedIn engagement metrics and individual posts.")

    # Section 1: LinkedIn Metrics
    st.header("📊 LinkedIn Metrics")
    if metrics_df is not None and not metrics_df.empty:
        # Display total impressions, clicks, and engagement
        st.subheader("Total Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_impressions = metrics_df['Impressions (total)'].sum()
            display_metric("Total Impressions", total_impressions,0)
        with col2:
            total_clicks = metrics_df['Clicks (total)'].sum()
            display_metric("Total Clicks", total_clicks,0)
        with col3:
            total_engagement = metrics_df['Engagement rate (total)'].mean()
            display_metric("Avg Engagement Rate", f"{total_engagement:.2f}%",0)

        # Plot impressions over time
        st.subheader("Impressions Over Time")
        fig = px.line(metrics_df, x='Date', y='Impressions (total)', title="Total Impressions Over Time")
        st.plotly_chart(fig, use_container_width=True)

        # Plot engagement rate over time
        st.subheader("Engagement Rate Over Time")
        fig = px.line(metrics_df, x='Date', y='Engagement rate (total)', title="Engagement Rate Over Time")
        st.plotly_chart(fig, use_container_width=True)

        # Impressions vs Clicks vs Engagement Rate
        st.subheader("📊 Impressions vs Clicks vs Engagement")
        fig = px.line(metrics_df, x="Date", y=["Impressions (total)", "Clicks (total)", "Engagement rate (total)"],
                      title="LinkedIn Performance Over Time")
        st.plotly_chart(fig, use_container_width=True)

        # Engagement Rate Histogram
        st.subheader("📊 Engagement Rate Distribution")
        fig = px.histogram(metrics_df, x="Engagement rate (total)", nbins=10, title="Distribution of Engagement Rate")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No LinkedIn metrics data found.")

    # Section 2: LinkedIn Posts
    st.header("📄 LinkedIn Posts")
    if posts_df is not None and not posts_df.empty:
        # Display top posts by impressions
        st.subheader("Top Posts by Impressions")
        top_posts = posts_df.sort_values(by='Impressions', ascending=False).head(10)
        st.dataframe(top_posts[['Post title', 'Impressions', 'Clicks', 'Engagement rate']])

        # Plot engagement metrics for top posts
        st.subheader("Engagement Metrics for Top Posts")
        fig = px.bar(top_posts, x='Post title', y=['Likes', 'Comments', 'Reposts'], 
                     title="Engagement Metrics for Top Posts")
        st.plotly_chart(fig, use_container_width=True)

        # Top Posts by Engagement Rate
        st.subheader("🔥 Top 5 Posts by Engagement Rate")
        top_posts = posts_df.sort_values(by="Engagement rate", ascending=False).head(5)
        st.dataframe(top_posts[['Post title', 'Impressions', 'Clicks', 'Engagement rate']])

        # Most Shared LinkedIn Posts
        st.subheader("🔄 Most Shared LinkedIn Posts")
        fig = px.bar(posts_df.sort_values(by="Reposts", ascending=False).head(10),
                     x="Post title", y="Reposts", title="Most Shared LinkedIn Posts")
        st.plotly_chart(fig, use_container_width=True)

        display_post_metrics(posts_df,metrics_df)
    else:
        st.warning("No LinkedIn posts data found.")

def page_youtube(youtube_data):
    st.title("📺 YouTube Metrics")
    st.markdown("This page shows the performance metrics for YouTube.")

    if youtube_data is not None and not youtube_data.empty:
        st.subheader("Engagement Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_views = youtube_data["Views"].sum()
            display_metric("Total Views", total_views, 0)
        with col2:
            total_likes = youtube_data["Likes"].sum()
            display_metric("Total Likes", total_likes, 0)
        with col3:
            total_comments = youtube_data["Comments"].sum()
            display_metric("Total Comments", total_comments, 0)

        st.subheader("Views Over Time")
        fig = px.line(youtube_data, x="Date", y="Views", title="Views Over Time")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top Videos by Views")
        top_videos = youtube_data.sort_values(by="Views", ascending=False).head(10)
        st.dataframe(top_videos)

def page_x(x_data):
    st.title("🐦 X (Twitter) Metrics")
    st.markdown("This page shows the performance metrics for X (formerly Twitter).")

    if x_data is not None and not x_data.empty:
        st.subheader("Engagement Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            total_tweets = x_data["Tweets"].sum()
            display_metric("Total Tweets", total_tweets, 0)
        with col2:
            total_retweets = x_data["Retweets"].sum()
            display_metric("Total Retweets", total_retweets, 0)
        with col3:
            total_likes = x_data["Likes"].sum()
            display_metric("Total Likes", total_likes, 0)

        st.subheader("Engagement Over Time")
        fig = px.line(x_data, x="Date", y="Engagement", title="Engagement Over Time")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top Tweets by Engagement")
        top_tweets = x_data.sort_values(by="Engagement", ascending=False).head(10)
        st.dataframe(top_tweets)

def calculate_post_metrics(posts_df):
    if posts_df is None or posts_df.empty:
        return None

    # Detect the correct date column
    possible_date_cols = ['date', 'Created date', 'Published date', 'Post Date']
    date_col = next((col for col in possible_date_cols if col in posts_df.columns), None)

    if not date_col:
        st.error("❌ No valid date column found in the LinkedIn posts dataset.")
        return None

    # Convert to datetime
    posts_df[date_col] = pd.to_datetime(posts_df[date_col])

    # Aggregate posts weekly
    posts_df['week'] = posts_df[date_col].dt.to_period('W').astype(str)
    weekly_posts = posts_df.groupby('week').size().reset_index(name='num_posts')

    # Calculate week-over-week growth
    weekly_posts['post_growth'] = weekly_posts['num_posts'].pct_change() * 100
    
    return weekly_posts

def display_post_metrics(posts_df, linkedin_metrics):
    if posts_df is None or posts_df.empty:
        st.warning("No LinkedIn post data available.")
        return

    weekly_posts = calculate_post_metrics(posts_df)
    if weekly_posts is None or weekly_posts.empty:
        return

    st.subheader("📈 LinkedIn Post Growth Metrics")
    
    col1, col2 = st.columns(2)

    with col1:
        latest_week = weekly_posts.iloc[-1] if not weekly_posts.empty else None
        num_posts = latest_week['num_posts'] if latest_week is not None else 0
        display_metric("📌 Posts This Week", num_posts, 0)

    with col2:
        post_growth = latest_week['post_growth'] if latest_week is not None else 0
        display_metric("📈 Post Growth (%)", f"{post_growth:.2f}%", post_growth)

    # Compare post growth with views and reach
    if linkedin_metrics is not None and not linkedin_metrics.empty:
        linkedin_metrics['week'] = pd.to_datetime(linkedin_metrics['Date']).dt.to_period('W').astype(str)
        weekly_metrics = linkedin_metrics.groupby('week')[['Impressions (total)', 'Clicks (total)']].sum().reset_index()
        weekly_data = weekly_posts.merge(weekly_metrics, on='week', how='left')

        st.subheader("📊 Weekly Post Trends vs Engagement")
        fig = px.line(weekly_data, x='week', y=['num_posts', 'Impressions (total)'],
                      title="Weekly Posts vs Impressions",
                      markers=True)
        fig.update_traces(line=dict(width=2))
        st.plotly_chart(fig, use_container_width=True)
        
@st.cache_data
def load_data(filename):
    try:
        data = pd.read_csv(filename)
        
        # Convert 'date' column to datetime format (YYYYMMDD -> YYYY-MM-DD)
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
        
        if data.empty:
            print(f"Warning: The file {filename} is empty.")
            return None  # Return None for empty files without showing a warning
        return data
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return None
    except Exception as e:
        print(f"Error loading data from {filename}: {e}")
        return None

def get_worksheet_data(all_data, worksheet_name, alternative_names=None):
    """
    Flexible worksheet lookup with alternative name options
    """
    if not alternative_names:
        alternative_names = []
    
    # Check primary name first
    if worksheet_name in all_data:
        return all_data[worksheet_name]
    
    # Check alternative names
    for name in alternative_names:
        if name in all_data:
            return all_data[name]
    
    # If not found, try case-insensitive match
    lower_name = worksheet_name.lower()
    for key in all_data.keys():
        if key.lower() == lower_name:
            return all_data[key]
    
    return None

def validate_worksheet(df, worksheet_name, required_columns=None):
    """
    Validate worksheet data and columns
    """
    if df is None:
        st.error(f"❌ Worksheet '{worksheet_name}' not found in the spreadsheet")
        return False
    
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            st.error(f"❌ Worksheet '{worksheet_name}' is missing required columns: {', '.join(missing)}")
            return False
    
    if df.empty:
        st.warning(f"⚠️ Worksheet '{worksheet_name}' is empty")
        return False
    
    return True


# Main function for the dashboard
def main():
    # Your Google Sheet configuration
    SHEET_URL = "https://docs.google.com/spreadsheets/d/17gv72J54TDcW9wSAtG0cKGXty0zxfgeKZVLEp65bYcc/edit#gid=1065654865"
    
    # Connect to Google Sheets
    gc = connect_to_google_sheets()
    if not gc:
        st.error("Failed to connect to Google Sheets")
        return
    
    # Show loading status
    with st.spinner("Loading data from Data Sources..."):
        # Load all data
        all_data = load_sheet_data(SHEET_URL)
        
        if not all_data:
            st.error("Failed to load data from Google Sheets")
            st.stop()
              
        # Debug: Show loaded worksheet names
        if st.secrets.get("DEBUG", False):
            st.write("Actual worksheet names:", list(all_data.keys()))
        
        # Load and validate each dataset
        loaded_data = {}
        for data_key, config in WORKSHEET_MAPPING.items():
            worksheet_name = config["primary"]  # Get the actual worksheet name string
            if worksheet_name in all_data:
                df = all_data[worksheet_name]  # Directly access the worksheet
                
                # Validate required columns
                missing_cols = [col for col in config.get("required_cols", []) 
                              if col not in df.columns]
                if missing_cols:
                    # st.warning(f"⚠️ Worksheet '{worksheet_name}' is missing columns: {', '.join(missing_cols)}")
                    # Create empty dataframe with required columns
                    df = pd.DataFrame(columns=config.get("required_cols", ["date"]))
                
                loaded_data[data_key] = df
            else:
                st.warning(f"⚠️ Worksheet '{worksheet_name}' not found. Using placeholder data for {data_key}")
                # Create empty dataframe with required columns
                loaded_data[data_key] = pd.DataFrame(columns=config.get("required_cols", ["date"]))
        
        # Map to variables with your actual worksheet names
        user_traffic_data = loaded_data["user_traffic"]
        engagement_data = loaded_data["engagement"]
        acquisition_data = loaded_data["acquisition"]
        page_views_data = loaded_data["page_views"]
        demographics_data = loaded_data["demographics"]
        device_data = loaded_data["device"]  # Using "technology" worksheet
        events_data = loaded_data["events"]
        site_speed_data = loaded_data["site_speed"]
        search_console_data = loaded_data["search_console"]  # Using "seo_top_queries"
        seo_pages_data = loaded_data["seo_pages"]  # Using "seo_top_pages"
        seo_content_data = loaded_data["seo_content"]  # Using "seo_content_engagement"
        organic_search_data = loaded_data["organic_search"]
        landing_pages_data = loaded_data["landing_pages"]  # Using "seo_landing_pages"
        
        # For worksheets that don't exist in your sheet but are referenced in code
        conversion_data = pd.DataFrame(columns=["date", "conversions", "totalRevenue"])
        ecommerce_data = pd.DataFrame(columns=["date", "productName", "itemRevenue"])
        ltv_data = pd.DataFrame(columns=["date", "userLifetimeBucket", "userLifetimeRevenue"])
        audience_data = pd.DataFrame(columns=["audienceName", "activeUsers", "conversions"])
        linkedin_posts = pd.DataFrame(columns=["Created date", "Post title", "Impressions"])
        linkedin_metrics = pd.DataFrame(columns=["Date", "Impressions (total)", "Clicks (total)"])
        facebook_data = pd.DataFrame(columns=["Publish time", "Title", "Reach"])
        instagram_data = pd.DataFrame(columns=["Date", "Title", "Reach"])
        youtube_data = pd.DataFrame(columns=["Date", "Title", "Views"])
        x_data = pd.DataFrame(columns=["Date", "Tweet", "Impressions"])
        ga4_data = pd.DataFrame(columns=["date", "sessions", "users"])
        seo_data = pd.DataFrame(columns=["Date", "Keyword", "Position"])
        
        # Verify we got data
        if not isinstance(all_data, dict) or len(all_data) == 0:
            st.error("No data found in the spreadsheet")
            st.stop()
               
        # Debug: Show loaded worksheet names
        if st.secrets.get("DEBUG", False):
            st.write("Loaded worksheets:", list(all_data.keys()))
        
        # Map to variables using proper worksheet names
        user_traffic_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["user_traffic"]["primary"],
            WORKSHEET_MAPPING["user_traffic"]["alternatives"]
        )

        engagement_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["engagement"]["primary"],
            WORKSHEET_MAPPING["engagement"]["alternatives"]
        )

        acquisition_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["acquisition"]["primary"],
            WORKSHEET_MAPPING["acquisition"]["alternatives"]
        )

        page_views_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["page_views"]["primary"],
            WORKSHEET_MAPPING["page_views"]["alternatives"]
        )

        demographics_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["demographics"]["primary"],
            WORKSHEET_MAPPING["demographics"]["alternatives"]
        )

        device_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["device"]["primary"],
            WORKSHEET_MAPPING["device"]["alternatives"]
        )

        events_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["events"]["primary"],
            WORKSHEET_MAPPING["events"]["alternatives"]
        )

        audience_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["audience"]["primary"],
            WORKSHEET_MAPPING["audience"]["alternatives"]
        )

        site_speed_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["site_speed"]["primary"],
            WORKSHEET_MAPPING["site_speed"]["alternatives"]
        )

        search_console_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["search_console"]["primary"],
            WORKSHEET_MAPPING["search_console"]["alternatives"]
        )

        seo_pages_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["seo_pages"]["primary"],
            WORKSHEET_MAPPING["seo_pages"]["alternatives"]
        )

        seo_content_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["seo_content"]["primary"],
            WORKSHEET_MAPPING["seo_content"]["alternatives"]
        )

        organic_search_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["organic_search"]["primary"],
            WORKSHEET_MAPPING["organic_search"]["alternatives"]
        )

        landing_pages_data = get_worksheet_data(
            all_data,
            WORKSHEET_MAPPING["landing_pages"]["primary"],
            WORKSHEET_MAPPING["landing_pages"]["alternatives"]
        )

        # For worksheets that don't exist in your sheet but are referenced in code
        conversion_data = pd.DataFrame(columns=["date", "conversions", "totalRevenue"])
        ecommerce_data = pd.DataFrame(columns=["date", "productName", "itemRevenue"])
        ltv_data = pd.DataFrame(columns=["date", "userLifetimeBucket", "userLifetimeRevenue"])
        linkedin_posts = pd.DataFrame(columns=["Created date", "Post title", "Impressions"])
        linkedin_metrics = pd.DataFrame(columns=["Date", "Impressions (total)", "Clicks (total)"])
        facebook_data = pd.DataFrame(columns=["Publish time", "Title", "Reach"])
        instagram_data = pd.DataFrame(columns=["Date", "Title", "Reach"])
        youtube_data = pd.DataFrame(columns=["Date", "Title", "Views"])
        x_data = pd.DataFrame(columns=["Date", "Tweet", "Impressions"])
        ga4_data = pd.DataFrame(columns=["date", "sessions", "users"])
        seo_data = pd.DataFrame(columns=["Date", "Keyword", "Position"])
        
        # Verify critical data is loaded
        if user_traffic_data is None:
            st.error(f"Worksheet '{WORKSHEET_MAPPING['user_traffic']}' not found")
            st.stop()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    
    # Create two main sections: SEO and SMM
    section = st.sidebar.radio("Select Section", ["Search Engine Optimization (SEO)", "Social Media Management (SMM)"])

    if section == "Search Engine Optimization (SEO)":
        # SEO Pages
        page = st.sidebar.radio(
            "Go to",
            [
                "Overview", "Acquisition", "Page Views", "Demographics", "Device & Technology",
                "Events", "E-commerce", "User Lifetime Value", "Audience & Segments", "App-Specific Data",
                "Funnel Analysis", "Retention & Cohorts", "Site Speed & Performance", "Error Tracking",
                "AI Insights", "Keyword Analysis", "SEO Metrics Overview"
            ]
        )
    elif section == "Social Media Management (SMM)":
        # SMM Pages
        page = st.sidebar.radio(
            "Choose Social Media",
            [
                "Overview", "Facebook", "Instagram", "LinkedIn Analysis", "YouTube", "X","Calendar"
            ]
        )
    
    # Date range filter
    st.sidebar.header("Date Filter")
    if user_traffic_data is not None and not user_traffic_data.empty:
        # Set the minimum date to February 15, 2025
        min_date = pd.to_datetime("2025-02-10").date()  # Fixed start date
        max_date = user_traffic_data['date'].max().date()  # Convert to datetime.date
        selected_date_range = st.sidebar.date_input(
            "Select Date Range",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    else:
        selected_date_range = None

    # Filter data based on selected date range
    if selected_date_range:
        start_date, end_date = selected_date_range
        user_traffic_data = filter_data_by_date(user_traffic_data, start_date, end_date)
        engagement_data = filter_data_by_date(engagement_data, start_date, end_date)
        acquisition_data = filter_data_by_date(acquisition_data, start_date, end_date)
        conversion_data = filter_data_by_date(conversion_data, start_date, end_date)
        page_views_data = filter_data_by_date(page_views_data, start_date, end_date)
        demographics_data = filter_data_by_date(demographics_data, start_date, end_date)

    # Display the selected page
    if section == "Search Engine Optimization (SEO)":
        if page == "Overview":
            page_overview(user_traffic_data, engagement_data, conversion_data)
        elif page == "Acquisition":
            page_acquisition(acquisition_data)
        elif page == "Page Views":
            page_page_views(page_views_data)
        elif page == "Demographics":
            page_demographics(demographics_data)
        elif page == "Device & Technology":
            page_device_technology(device_data)
        elif page == "Events":
            page_events(events_data)
        elif page == "E-commerce":
            page_ecommerce(ecommerce_data)
        elif page == "User Lifetime Value":
            page_ltv(ltv_data)
        elif page == "Audience & Segments":
            page_audience(audience_data)
        elif page == "App-Specific Data":
            page_app(app_data)
        elif page == "Funnel Analysis":
            page_funnel(funnel_data)
        elif page == "Retention & Cohorts":
            page_retention(retention_data)
        elif page == "Site Speed & Performance":
            page_site_speed(site_speed_data)
        elif page == "Error Tracking":
            page_error_tracking(error_data)
        elif page == "AI Insights":
            page_deepseek_ai(user_traffic_data, conversion_data, demographics_data, device_data, events_data, ecommerce_data, ltv_data, audience_data, app_data, funnel_data, retention_data, site_speed_data, error_data)
        elif page == "Keyword Analysis":
            page_search_console(search_console_data)
        elif page == "SEO Metrics Overview":
            page_seo_overview(search_console_data, ga4_data, seo_data)

    elif section == "Social Media Management (SMM)":
        if page == "Overview":
            page_smm_overview(facebook_data, instagram_data, linkedin_metrics, linkedin_posts,youtube_data, x_data)
        elif page == "Facebook":
            page_facebook(facebook_data)
        elif page == "Instagram":
            page_instagram(instagram_data)
        elif page == "LinkedIn Analysis":
            page_linkedin_analysis(linkedin_metrics, linkedin_posts)
        elif page == "YouTube":
            page_youtube(youtube_data)
        elif page == "X":
            page_x(x_data)
        elif page == "Calendar":
            show_social_media_calendar(facebook_data, instagram_data, linkedin_posts)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
        **Digital Marketing & SEO Dashboard**  
        Built with ❤️ using **Streamlit** and **Google Analytics Data API**.
    """)

    # Add a refresh button in the sidebar
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()  # Clear cached data to force a refresh
        if refresh_data():  # Ensure this calls the updated function
            st.rerun()



if __name__ == "__main__":
    main()