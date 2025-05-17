import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_search_console(search_console_data):
    st.title("🔍 Search Analytics")
    st.markdown("This page shows search performance data from Google Analytics 4.")
    
    # Check for empty data
    if search_console_data is None or search_console_data.empty:
        st.warning("No search analytics data available.")
        return
    
    # Ensure proper column names (handle case sensitivity)
    search_console_data.columns = search_console_data.columns.str.lower()
    
    # Calculate additional metrics
    search_console_data['ctr'] = (search_console_data['activeusers'] / 
                                 search_console_data['screenpageviews']).fillna(0)
    
    st.header("📊 Search Performance Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_views = search_console_data["screenpageviews"].sum()
        display_metric("Total Page Views", total_views, 0)
    with col2:
        total_users = search_console_data["activeusers"].sum()
        display_metric("Total Users", total_users, 0)
    with col3:
        avg_ctr = (search_console_data["activeusers"].sum() / 
                  search_console_data["screenpageviews"].sum() * 100) if total_views > 0 else 0
        display_metric("Avg CTR", f"{avg_ctr:.2f}%", 0)

    st.subheader("Top Performing Search Terms")
    tab1, tab2, tab3 = st.tabs(["By Page Views", "By Users", "By CTR"])
    
    with tab1:
        top_views = search_console_data.sort_values("screenpageviews", ascending=False).head(10)
        fig = px.bar(top_views, x="searchterm", y="screenpageviews",
                    title="Top Search Terms by Page Views",
                    labels={'searchterm': 'Search Term', 'screenpageviews': 'Page Views'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        top_users = search_console_data.sort_values("activeusers", ascending=False).head(10)
        fig = px.bar(top_users, x="searchterm", y="activeusers",
                    title="Top Search Terms by Active Users",
                    labels={'searchterm': 'Search Term', 'activeusers': 'Active Users'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Filter for terms with minimum page views
        min_views = 50  # Adjust this threshold as needed
        high_ctr = search_console_data[search_console_data["screenpageviews"] > min_views].nlargest(10, "ctr")
        fig = px.bar(high_ctr, x="searchterm", y="ctr",
                    title=f"Top Search Terms by CTR (min {min_views} views)",
                    labels={'searchterm': 'Search Term', 'ctr': 'CTR'})
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Page Path Performance")
    tab4, tab5 = st.tabs(["By Search Term", "Overall"])
    
    with tab4:
        selected_term = st.selectbox(
            "Select a search term to analyze:",
            options=search_console_data["searchterm"].unique(),
            index=0
        )
        term_data = search_console_data[search_console_data["searchterm"] == selected_term]
        if not term_data.empty:
            fig = px.bar(term_data, x="pagepath", y="screenpageviews",
                        title=f"Page Performance for: '{selected_term}'",
                        labels={'pagepath': 'Page Path', 'screenpageviews': 'Page Views'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for selected search term.")
    
    with tab5:
        page_performance = search_console_data.groupby("pagepath").agg({
            "screenpageviews": "sum",
            "activeusers": "sum"
        }).reset_index().sort_values("screenpageviews", ascending=False).head(10)
        
        fig = px.bar(page_performance, x="pagepath", y="screenpageviews",
                    title="Top Performing Pages from Search",
                    labels={'pagepath': 'Page Path', 'screenpageviews': 'Total Page Views'})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Trend Analysis")
    time_group = st.radio(
        "Group by:",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True
    )
    
    # Prepare time-based grouping
    search_console_data['date'] = pd.to_datetime(search_console_data['date'])
    if time_group == "Weekly":
        grouped_data = search_console_data.groupby(pd.Grouper(key='date', freq='W-MON')).sum().reset_index()
    elif time_group == "Monthly":
        grouped_data = search_console_data.groupby(pd.Grouper(key='date', freq='M')).sum().reset_index()
    else:  # Daily
        grouped_data = search_console_data.groupby('date').sum().reset_index()
    
    fig = px.line(grouped_data, x='date', y=['screenpageviews', 'activeusers'],
                title=f"Search Performance Trend ({time_group})",
                labels={'value': 'Count', 'variable': 'Metric'})
    st.plotly_chart(fig, use_container_width=True)