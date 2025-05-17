import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_ecommerce(ecommerce_data):
    st.title("🛒 E-commerce")
    st.markdown("This page shows the performance of e-commerce products.")

    if ecommerce_data is None or ecommerce_data.empty:
        st.warning("No e-commerce data available.")
        return

    st.header("💰 Revenue Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_revenue = ecommerce_data["itemRevenue"].sum()
        display_metric("Total Revenue", f"${total_revenue:,.2f}", 0)
    with col2:
        avg_order_value = total_revenue / len(ecommerce_data) if len(ecommerce_data) > 0 else 0
        display_metric("Average Order Value", f"${avg_order_value:,.2f}", 0)
    with col3:
        unique_products = ecommerce_data["productName"].nunique()
        display_metric("Unique Products Sold", unique_products, 0)

    st.header("📊 Product Performance")
    product_stats = ecommerce_data.groupby("productName").agg({
        "itemRevenue": "sum",
        "productName": "count"
    }).rename(columns={
        "itemRevenue": "total_revenue",
        "productName": "units_sold"
    }).sort_values("total_revenue", ascending=False)

    tab1, tab2 = st.tabs(["By Revenue", "By Units Sold"])
    with tab1:
        st.subheader("Top Products by Revenue")
        fig = px.bar(product_stats.head(10), x=product_stats.index, y="total_revenue",
                     title="Top 10 Products by Revenue", color="total_revenue")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Top Products by Units Sold")
        fig = px.bar(product_stats.sort_values("units_sold", ascending=False).head(10), 
                     x=product_stats.index, y="units_sold",
                     title="Top 10 Products by Units Sold", color="units_sold")
        st.plotly_chart(fig, use_container_width=True)

    if "date" in ecommerce_data.columns:
        st.header("⏱ Revenue Trends")
        ecommerce_data["date"] = pd.to_datetime(ecommerce_data["date"])
        daily_revenue = ecommerce_data.groupby("date")["itemRevenue"].sum().reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Daily Revenue")
            fig = px.line(daily_revenue, x="date", y="itemRevenue", 
                          title="Daily Revenue Trend")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Revenue by Day of Week")
            daily_revenue["day_of_week"] = daily_revenue["date"].dt.day_name()
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            revenue_by_day = daily_revenue.groupby("day_of_week")["itemRevenue"].sum().reset_index()
            revenue_by_day["day_of_week"] = pd.Categorical(revenue_by_day["day_of_week"], categories=day_order, ordered=True)
            revenue_by_day = revenue_by_day.sort_values("day_of_week")
            
            fig = px.bar(revenue_by_day, x="day_of_week", y="itemRevenue",
                         title="Revenue by Day of Week")
            st.plotly_chart(fig, use_container_width=True)