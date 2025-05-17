import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta


def display_metric(label, value, delta=None, delta_prefix=""):
    """
    Display a metric card with optional delta indicator
    
    Args:
        label (str): Metric name/title
        value (str|int|float): The main value to display
        delta (str|int|float|None): Delta value for comparison
        delta_prefix (str): Prefix text for delta (e.g., "vs ")
    """
    # Convert value to string if it's numeric
    if isinstance(value, (int, float)):
        display_value = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
    else:
        display_value = str(value)
    
    # Handle delta comparison safely
    delta_display = None
    if delta is not None:
        try:
            # Try to convert delta to float for comparison
            delta_num = float(delta)
            delta_display = f"{delta_prefix}{delta_num:+,}" if isinstance(delta_num, int) else f"{delta_prefix}{delta_num:+,.2f}"
        except (ValueError, TypeError):
            # Fallback to string representation if conversion fails
            delta_display = f"{delta_prefix}{delta}"
    
    st.metric(
        label=label,
        value=display_value,
        delta=delta_display
    )


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

def add_metric_styles():
    """Add custom CSS styles for metrics"""
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

def filter_data_by_date(data, start_date, end_date):
    """Filter DataFrame by date range"""
    if data is None or data.empty or 'date' not in data.columns:
        return data
    
    mask = (data['date'] >= pd.to_datetime(start_date)) & (data['date'] <= pd.to_datetime(end_date))
    return data.loc[mask]

def calculate_delta(current_value, previous_value):
    """Calculate percentage change between values"""
    if previous_value == 0:
        return 0.0
    return ((current_value - previous_value) / previous_value) * 100

