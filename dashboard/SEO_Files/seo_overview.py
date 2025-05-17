import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric, calculate_delta

def safe_mean(series, default=0):
    """Calculate mean with empty series handling"""
    return series.mean() if not series.empty else default

def safe_sum(series, default=0):
    """Calculate sum with empty series handling"""
    return series.sum() if not series.empty else default

def page_overview(user_traffic_data, engagement_data, conversion_data):
    st.title("📊 Overview")
    st.markdown("""
        Welcome to the **Digital Marketing & SEO Dashboard**!  
        This page provides a high-level overview of your website's performance.
    """)

    # User & Traffic Data Section
    if user_traffic_data is not None and not user_traffic_data.empty:
        st.header("🚦 User & Traffic Data")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            activeUsers = safe_sum(user_traffic_data.get("activeUsers", pd.Series()))
            previous_activeUsers = safe_sum(user_traffic_data.get("activeUsers", pd.Series()).shift(7))
            delta_users = calculate_delta(activeUsers, previous_activeUsers)
            display_metric("Active Users", activeUsers, delta_users)
            
        with col2:
            # Calculate engagement rate as a proxy for bounce rate
            engaged_rate = (safe_sum(user_traffic_data.get("engagedSessions", pd.Series())) / 
                          safe_sum(user_traffic_data.get("sessions", pd.Series()))) * 100
            previous_engaged_rate = (safe_sum(user_traffic_data.get("engagedSessions", pd.Series()).shift(7)) / \
                                  (safe_sum(user_traffic_data.get("sessions", pd.Series()).shift(7)) or 1)) * 100
            delta_engaged_rate = calculate_delta(engaged_rate, previous_engaged_rate)
            display_metric("Engagement Rate", f"{engaged_rate:.1f}%", delta_engaged_rate)
            
        with col3:
            total_sessions = safe_sum(user_traffic_data.get("sessions", pd.Series()))
            previous_sessions = safe_sum(user_traffic_data.get("sessions", pd.Series()).shift(7))
            delta_sessions = calculate_delta(total_sessions, previous_sessions)
            display_metric("Total Sessions", total_sessions, delta_sessions)

        # Plot only if we have date and activeUsers columns
        if all(col in user_traffic_data.columns for col in ["date", "activeUsers"]):
            st.subheader("Active Users Over Time")
            fig = px.bar(user_traffic_data, x="date", y="activeUsers", 
                         title="Active Users Over Time")
            st.plotly_chart(fig, use_container_width=True)

    # Engagement Data Section
    if engagement_data is not None and not engagement_data.empty:
        st.header("🎯 User Engagement & Behavior")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_duration = safe_mean(engagement_data.get("userEngagementDuration", pd.Series()))
            previous_duration = safe_mean(engagement_data.get("userEngagementDuration", pd.Series()).shift(7))
            delta_duration = calculate_delta(avg_duration, previous_duration)
            display_metric("Avg Engagement Duration", 
                          f"{avg_duration:.1f} sec", 
                          delta_duration)
            
        with col2:
            # Calculate pages per session if we have both datasets
            if (user_traffic_data is not None and not user_traffic_data.empty and
                'screenPageViews' in engagement_data.columns and 
                'sessions' in user_traffic_data.columns):
                pages_per_session = (safe_sum(engagement_data['screenPageViews']) / 
                                safe_sum(user_traffic_data['sessions']))
                prev_pages = (safe_sum(engagement_data['screenPageViews'].shift(7))) / \
                            (safe_sum(user_traffic_data['sessions'].shift(7)) or 1)
                delta_pages = calculate_delta(pages_per_session, prev_pages)
                display_metric("Pages per Session", 
                            f"{pages_per_session:.1f}", 
                            delta_pages)
            else:
                st.metric("Pages per Session", "N/A")

                
        with col3:
            total_events = safe_sum(engagement_data.get("eventCount", pd.Series()))
            previous_events = safe_sum(engagement_data.get("eventCount", pd.Series()).shift(7))
            delta_events = calculate_delta(total_events, previous_events)
            display_metric("Total Events", total_events, delta_events)

        # Event count plot
        if all(col in engagement_data.columns for col in ["date", "eventCount"]):
            st.subheader("Event Count Over Time")
            fig = px.bar(engagement_data, x="date", y="eventCount", 
                         title="Event Count Over Time")
            st.plotly_chart(fig, use_container_width=True)

    # Conversion Data Section
    if conversion_data is not None and not conversion_data.empty:
        st.header("💰 Conversion & Goal Tracking")
        col1, col2 = st.columns(2)  # Reduced to 2 columns since we don't have conversion rate
        
        with col1:
            total_conversions = safe_sum(conversion_data.get("conversions", pd.Series()))
            previous_conversions = safe_sum(conversion_data.get("conversions", pd.Series()).shift(7))
            delta_conversions = calculate_delta(total_conversions, previous_conversions)
            display_metric("Total Conversions", total_conversions, delta_conversions)
            
        with col2:
            total_revenue = safe_sum(conversion_data.get("totalRevenue", pd.Series()))
            previous_revenue = safe_sum(conversion_data.get("totalRevenue", pd.Series()).shift(7))
            delta_revenue = calculate_delta(total_revenue, previous_revenue)
            display_metric("Total Revenue", f"${total_revenue:,.2f}", delta_revenue)

        # Conversions plot
        if all(col in conversion_data.columns for col in ["date", "conversions"]):
            st.subheader("Conversions Over Time")
            fig = px.line(conversion_data, x="date", y="conversions", 
                         title="Conversions Over Time")
            st.plotly_chart(fig, use_container_width=True)