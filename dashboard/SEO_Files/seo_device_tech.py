import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_device_technology(device_data):
    st.title("📱 Device & Technology")
    st.markdown("This page shows the breakdown of users by device and technology.")
    
    if device_data is None or device_data.empty:
        st.warning("No device & technology data available.")
        return
    
    available_cols = device_data.columns.tolist()
    
    metric_col = "activeUsers" if "activeUsers" in available_cols else None
    if not metric_col:
        numeric_cols = device_data.select_dtypes(include=['number']).columns
        metric_col = numeric_cols[0] if len(numeric_cols) > 0 else None
    
    if not metric_col:
        st.error("No numeric columns found for analysis")
        return
    
    st.subheader(f"User Distribution by {metric_col}")
    
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
    
    if "browser" in available_cols:
        st.subheader("By Browser")
        browser_data = device_data.groupby("browser")[metric_col].sum().nlargest(10).reset_index()
        fig = px.bar(browser_data, x="browser", y=metric_col, color="browser",
                     title=f"Top 10 Browsers by {metric_col}")
        st.plotly_chart(fig, use_container_width=True)
    
    if all(col in available_cols for col in ["operatingSystem", "browser"]):
        st.subheader("OS & Browser Combinations")
        combo_data = device_data.groupby(["operatingSystem", "browser"])[metric_col].sum().nlargest(15).reset_index()
        combo_data["combo"] = combo_data["operatingSystem"] + " + " + combo_data["browser"]
        fig = px.bar(combo_data, x="combo", y=metric_col, color="operatingSystem",
                     title=f"Top 15 OS+Browser Combos by {metric_col}")
        st.plotly_chart(fig, use_container_width=True)
    
    if "date" in available_cols:
        st.subheader("Technology Trends Over Time")
        time_data = device_data.groupby(["date", "deviceCategory"])[metric_col].sum().reset_index()
        fig = px.line(time_data, x="date", y=metric_col, color="deviceCategory",
                      title=f"{metric_col} Trends by Device Category")
        st.plotly_chart(fig, use_container_width=True)