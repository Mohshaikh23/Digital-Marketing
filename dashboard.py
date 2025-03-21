# dashboard.py
import streamlit as st
st.set_page_config(page_title="Digital Marketing & SEO Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from data_extractor import main as refresh_data
import requests
import json
import plotly.express as px
from data_extractor import load_linkedin_excel_data
from streamlit_calendar import calendar


# Load data from CSV files and convert date format
def load_data(filename):
    try:
        data = pd.read_csv(filename)
        
        # Convert 'date' column to datetime format (YYYYMMDD -> YYYY-MM-DD)
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
        
        if data.empty:
            return None  # Return None for empty files without showing a warning
        return data
    except Exception as e:
        return None  # Return None for missing or invalid files without showing an error

# Function to calculate week-over-week (WoW) and month-over-month (MoM) growth
def calculate_growth(data, metric):
    if data is None or data.empty:
        return None
    
    # Calculate WoW growth
    data['WoW Growth'] = data[metric].pct_change(periods=7) * 100
    
    # Calculate MoM growth
    data['MoM Growth'] = data[metric].pct_change(periods=30) * 100
    
    return data

# Function to calculate delta values for metrics
def calculate_delta(current_value, previous_value):
    if previous_value == 0:
        return 0
    return ((current_value - previous_value) / previous_value) * 100

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

# Function to filter data based on date range
def filter_data_by_date(data, start_date, end_date):
    if data is None or data.empty:
        return data
    # Convert start_date and end_date to pandas.Timestamp
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return data[(data['date'] >= start_date) & (data['date'] <= end_date)]

# Add this function to load social media data
def load_social_media_data(filename):
    try:
        data = pd.read_excel(filename)
        if data.empty:
            print(f"Warning: The file {filename} is empty.")
            return None
        return data
    except Exception as e:
        print(f"Error loading data from {filename}: {e}")
        return None

def load_linkedin_data():
    try:
        # Load LinkedIn posts
        with open("linkedin_posts.json", "r") as f:
            linkedin_posts = json.load(f)

        # Load LinkedIn engagement metrics
        with open("linkedin_engagement_metrics.json", "r") as f:
            linkedin_engagement_metrics = json.load(f)

        return linkedin_posts, linkedin_engagement_metrics
    except Exception as e:
        print(f"Error loading LinkedIn data: {e}")
        return None, None


def load_facebook_data(filename):
    try:
        # Load Facebook data from CSV file
        facebook_data = pd.read_csv(filename)

        # Rename "Reactions" column to "Likes" for consistency in the dashboard
        if "Reactions" in facebook_data.columns:
            facebook_data.rename(columns={"Reactions": "Likes"}, inplace=True)

        # Convert 'Publish time' to datetime format
        if "Publish time" in facebook_data.columns:
            facebook_data["Publish time"] = pd.to_datetime(facebook_data["Publish time"], errors='coerce')

        return facebook_data
    except Exception as e:
        print(f"Error loading Facebook data: {e}")
        return None


def load_instagram_data(filename):
    try:
        # Load Instagram data from CSV file
        instagram_data = pd.read_csv(filename)
        return instagram_data
    except Exception as e:
        print(f"Error loading Instagram data: {e}")
        return None

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
    st.title("📄 Page Views")
    st.markdown("This page shows the most viewed pages on your website.")

    if page_views_data is not None and not page_views_data.empty:
        # Top 10 Pages by Views
        st.subheader("Top 10 Pages by Views")
        top_pages = page_views_data.groupby("pageTitle")["screenPageViews"].sum().nlargest(10).reset_index()
        fig = px.bar(top_pages, x="pageTitle", y="screenPageViews", title="Top 10 Pages by Views")
        st.plotly_chart(fig, use_container_width=True)

# Page 4: Demographics
def page_demographics(demographics_data):
    st.title("👥 Demographics")
    st.markdown("This page shows the demographic breakdown of your users.")

    if demographics_data is not None and not demographics_data.empty:
        # Group by age bracket and gender
        st.subheader("Active Users by Age Bracket")
        age_data = demographics_data.groupby("userAgeBracket")["activeUsers"].sum().reset_index()
        fig = px.bar(age_data, x="userAgeBracket", y="activeUsers", title="Active Users by Age Bracket")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Active Users by Gender")
        gender_data = demographics_data.groupby("userGender")["activeUsers"].sum().reset_index()
        fig = px.pie(gender_data, values="activeUsers", names="userGender", title="Active Users by Gender")
        st.plotly_chart(fig, use_container_width=True)

        # Group by country
        st.subheader("Active Users by Country")
        country_data = demographics_data.groupby("country")["activeUsers"].sum().reset_index()
        fig = px.choropleth(
            country_data,
            locations="country",  # Column with country names
            locationmode="country names",  # Use country names for mapping
            color="activeUsers",  # Column to determine color intensity
            hover_name="country",  # Column to display on hover
            title="Active Users by Country"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No demographics data available.")

# Page 5: Device & Technology
def page_device_technology(device_data):
    st.title("📱 Device & Technology")
    st.markdown("This page shows the breakdown of users by device and technology.")

    if device_data is not None and not device_data.empty:
        # Group by device category
        st.subheader("Active Users by Device Category")
        device_category_data = device_data.groupby("deviceCategory")["activeUsers"].sum().reset_index()
        fig = px.bar(device_category_data, x="deviceCategory", y="activeUsers", title="Active Users by Device Category")
        st.plotly_chart(fig, use_container_width=True)

        # Group by operating system
        st.subheader("Active Users by Operating System")
        os_data = device_data.groupby("operatingSystem")["activeUsers"].sum().reset_index()
        fig = px.pie(os_data, values="activeUsers", names="operatingSystem", title="Active Users by Operating System")
        st.plotly_chart(fig, use_container_width=True)

        # Group by browser
        st.subheader("Active Users by Browser")
        browser_data = device_data.groupby("browser")["activeUsers"].sum().reset_index()
        fig = px.bar(browser_data, x="browser", y="activeUsers", title="Active Users by Browser")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No device & technology data available.")

# Page 6: Events
def page_events(events_data):
    st.title("🎯 Events")
    st.markdown("This page shows the breakdown of events triggered by users.")

    if events_data is not None and not events_data.empty:
        # Group by event name
        st.subheader("Event Count by Event Name")
        event_count_data = events_data.groupby("eventName")["eventCount"].sum().reset_index()
        fig = px.bar(event_count_data, x="eventName", y="eventCount", title="Event Count by Event Name")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No events data available.")

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
def page_ltv(ltv_data):
    st.title("💰 User Lifetime Value (LTV)")
    st.markdown("This page shows the lifetime value of users.")

    if ltv_data is not None and not ltv_data.empty:
        # Group by lifetime bucket
        st.subheader("Lifetime Revenue by User Bucket")
        ltv_revenue_data = ltv_data.groupby("userLifetimeBucket")["userLifetimeRevenue"].sum().reset_index()
        fig = px.bar(ltv_revenue_data, x="userLifetimeBucket", y="userLifetimeRevenue", title="Lifetime Revenue by User Bucket")
        st.plotly_chart(fig, use_container_width=True)

        # Group by lifetime transactions
        st.subheader("Lifetime Transactions by User Bucket")
        ltv_transactions_data = ltv_data.groupby("userLifetimeBucket")["userLifetimeTransactions"].sum().reset_index()
        fig = px.bar(ltv_transactions_data, x="userLifetimeBucket", y="userLifetimeTransactions", title="Lifetime Transactions by User Bucket")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No LTV data available.")

# Page 9: Audience & Segments
def page_audience(audience_data):
    st.title("👥 Audience & Segments")
    st.markdown("This page shows the performance of audience segments.")

    if audience_data is not None and not audience_data.empty:
        # Check if 'audienceName' column exists
        if "audienceName" in audience_data.columns:
            # Group by audience name
            st.subheader("Active Users by Audience")
            audience_users_data = audience_data.groupby("audienceName")["activeUsers"].sum().reset_index()
            fig = px.bar(audience_users_data, x="audienceName", y="activeUsers", title="Active Users by Audience")
            st.plotly_chart(fig, use_container_width=True)

            # Group by conversions
            st.subheader("Conversions by Audience")
            audience_conversions_data = audience_data.groupby("audienceName")["conversions"].sum().reset_index()
            fig = px.pie(audience_conversions_data, values="conversions", names="audienceName", title="Conversions by Audience")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("The 'audienceName' column is missing in the audience data.")
    else:
        st.warning("No audience & segments data available.")

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

# Main function for the dashboard
def main():
    # Load data
    user_traffic_data = load_data("analytics_data/user_traffic_data.csv")
    engagement_data = load_data("analytics_data/engagement_data.csv")
    acquisition_data = load_data("analytics_data/acquisition_data.csv")
    conversion_data = load_data("analytics_data/conversion_data.csv")
    page_views_data = load_data("analytics_data/page_views_data.csv")
    demographics_data = load_data("analytics_data/demographics_data.csv")
    device_data = load_data("analytics_data/device_data.csv")
    events_data = load_data("analytics_data/events_data.csv")
    ecommerce_data = load_data("analytics_data/ecommerce_data.csv")
    ltv_data = load_data("analytics_data/ltv_data.csv")
    audience_data = load_data("analytics_data/audience_data.csv")
    app_data = load_data("analytics_data/app_data.csv")
    funnel_data = load_data("analytics_data/funnel_data.csv")
    retention_data = load_data("analytics_data/retention_data.csv")
    site_speed_data = load_data("analytics_data/site_speed_data.csv")
    error_data = load_data("analytics_data/error_data.csv")
    search_console_data = load_data("analytics_data/search_console_data.csv")
    search_console_data = load_data('analytics_data/search_console_data.csv')
    ga4_data = load_data('analytics_data/ga4_data.csv')
    seo_data = load_data('analytics_data/seo_data.csv')
    
    # Load social media data
    linkedin_metrics, linkedin_posts = load_linkedin_excel_data("social_media_data/pro-efficient-data-entry_content_1742193384396.xlsx")
    facebook_data = load_facebook_data("social_media_data/Feb-01-2025_Mar-15-2025_613168031534769.csv")
    instagram_data = load_instagram_data("social_media_data/Feb-01-2025_Mar-15-2025_613168031534769.csv")
    youtube_data = load_social_media_data("social_media_data/youtube_data.xlsx")
    x_data = load_social_media_data("social_media_data/x_data.xlsx")

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
        refresh_data()  # Call the main function from data_extractor.py
        st.rerun()  # Rerun the app to reflect the updated data


if __name__ == "__main__":
    main()