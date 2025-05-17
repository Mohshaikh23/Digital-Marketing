import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_demographics(demographics_data):
    st.title("👥 User Demographics & Acquisition")
    st.markdown("This page shows user demographics and acquisition patterns.")
    
    if demographics_data is None or demographics_data.empty:
        st.warning("No demographics data available.")
        return

    available_cols = demographics_data.columns.tolist()
    
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
    
    st.header("📈 Acquisition Channels")
    if "firstUserSourceMedium" in available_cols:
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