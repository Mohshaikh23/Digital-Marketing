import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from Shared_Components.components import display_metric, calculate_delta

def page_events(events_data):
    st.title("🎯 User Events Analysis")
    st.markdown("This page provides comprehensive insights into user events and interactions.")
    
    if events_data is None or events_data.empty:
        st.warning("No events data available.")
        return

    available_cols = events_data.columns.tolist()
    
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

    st.header("📈 Event Distribution")
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
    
    if "date" in available_cols:
        st.header("⏱ Event Trends Over Time")
        events_data["date"] = pd.to_datetime(events_data["date"])
        events_data["week"] = events_data["date"].dt.to_period('W')
        weekly_events = events_data.groupby("week")["eventCount"].sum().reset_index()
        weekly_events["pct_change"] = weekly_events["eventCount"].pct_change() * 100
        
        current_week_data = weekly_events.iloc[-1] if len(weekly_events) > 0 else None
        
        daily_events = events_data.groupby("date")["eventCount"].sum().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            delta_value = current_week_data["pct_change"] if current_week_data is not None else 0
            current_week_count = current_week_data["eventCount"] if current_week_data is not None else "N/A"
            
            display_metric("Weekly Event Volume", 
                         f"{current_week_count:,}" if current_week_data is not None else "N/A", 
                         delta_value)
            
            fig = px.line(daily_events, x="date", y="eventCount",
                         title="Daily Event Volume Trend")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            events_data["day_of_week"] = events_data["date"].dt.day_name()
            weekly_pattern = events_data.groupby("day_of_week")["eventCount"].sum().reset_index()
            
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekly_pattern = weekly_pattern.set_index("day_of_week").loc[day_order].reset_index()
            weekly_pattern["pct_change"] = weekly_pattern["eventCount"].pct_change() * 100
            
            fig = px.bar(weekly_pattern, x="day_of_week", y="eventCount",
                         category_orders={"day_of_week": day_order},
                         title="Events by Day of Week")
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Top Events Over Time")
        top_events_over_time = events_data.groupby(["date", "eventName"])["eventCount"].sum().reset_index()
        top_5_events = event_count_data.nlargest(5, "eventCount")["eventName"].tolist()
        filtered_events = top_events_over_time[top_events_over_time["eventName"].isin(top_5_events)]
        
        event_deltas = []
        for event in top_5_events:
            event_data = filtered_events[filtered_events["eventName"] == event]
            if len(event_data) > 1:
                delta = (event_data.iloc[-1]["eventCount"] - event_data.iloc[-2]["eventCount"]) / event_data.iloc[-2]["eventCount"] * 100
            else:
                delta = 0
            event_deltas.append(delta)
        
        cols = st.columns(len(top_5_events))
        for i, (event, delta) in enumerate(zip(top_5_events, event_deltas)):
            event_count = event_count_data[event_count_data["eventName"] == event]["eventCount"].values[0]
            with cols[i]:
                display_metric(f"{event}", f"{event_count:,}", delta)
        
        fig = px.line(filtered_events, x="date", y="eventCount", color="eventName",
                     title="Trend of Top 5 Events Over Time")
        st.plotly_chart(fig, use_container_width=True)