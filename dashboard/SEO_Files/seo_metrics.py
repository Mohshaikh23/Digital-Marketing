import streamlit as st
import pandas as pd
import plotly.express as px
from Shared_Components.components import display_metric

def page_seo_overview(search_console_data, ga4_data, seo_data):
    st.title("📊 SEO Metrics Overview")
    st.markdown("This page provides an overview of key SEO metrics.")

    # Standardize column names to lowercase and check data availability
    def prepare_data(df):
        if df is None or df.empty:
            return None
        df.columns = df.columns.str.lower()
        return df

    search_console_data = prepare_data(search_console_data)
    ga4_data = prepare_data(ga4_data)
    seo_data = prepare_data(seo_data)

    # Create expandable sections for better organization
    with st.expander("🔍 Search Performance", expanded=True):
        if search_console_data is None:
            st.warning("No Search Console data available")
        else:
            # Calculate metrics only if columns exist
            has_clicks = 'clicks' in search_console_data.columns
            has_impressions = 'impressions' in search_console_data.columns
            has_position = 'position' in search_console_data.columns
            
            cols = st.columns(3)
            with cols[0]:
                total_clicks = search_console_data["clicks"].sum() if has_clicks else 0
                display_metric("Total Clicks", total_clicks, f"vs previous period | {total_clicks:,}")            
            
            with cols[1]:
                total_impressions = search_console_data["impressions"].sum() if has_impressions else 0
                display_metric("Total Impressions", total_impressions, "vs previous period", f"{total_impressions:,}")
            
            with cols[2]:
                avg_position = search_console_data["position"].mean() if has_position else 0
                display_metric("Avg Position", avg_position, "", f"{avg_position:.1f}")

            # Only show visualizations if we have meaningful data
            if has_clicks or has_impressions:
                st.subheader("Performance Over Time")
                time_col1, time_col2 = st.columns(2)
                
                with time_col1:
                    if has_clicks:
                        fig = px.line(search_console_data, x='date', y='clicks', 
                                    title="Daily Clicks Trend")
                        st.plotly_chart(fig, use_container_width=True)
                
                with time_col2:
                    if has_impressions:
                        fig = px.line(search_console_data, x='date', y='impressions', 
                                    title="Daily Impressions Trend")
                        st.plotly_chart(fig, use_container_width=True)

            if 'query' in search_console_data.columns and (has_clicks or has_impressions):
                st.subheader("Top Performing Queries")
                query_tab1, query_tab2 = st.tabs(["By Clicks", "By Impressions"])
                
                with query_tab1:
                    if has_clicks:
                        top_queries = search_console_data.groupby('query')['clicks'].sum().nlargest(10).reset_index()
                        fig = px.bar(top_queries, x='query', y='clicks', 
                                    title="Top Queries by Clicks",
                                    labels={'query': 'Search Query', 'clicks': 'Total Clicks'})
                        st.plotly_chart(fig, use_container_width=True)
                
                with query_tab2:
                    if has_impressions:
                        top_queries = search_console_data.groupby('query')['impressions'].sum().nlargest(10).reset_index()
                        fig = px.bar(top_queries, x='query', y='impressions', 
                                    title="Top Queries by Impressions",
                                    labels={'query': 'Search Query', 'impressions': 'Total Impressions'})
                        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📈 User Engagement", expanded=True):
        if ga4_data is None:
            st.warning("No Google Analytics data available")
        else:
            # Calculate GA4 metrics
            has_views = 'screenpageviews' in ga4_data.columns
            has_users = 'activeusers' in ga4_data.columns
            
            cols = st.columns(3)
            with cols[0]:
                total_views = ga4_data['screenpageviews'].sum() if has_views else 0
                display_metric("Total Page Views", total_views, "vs previous period", f"{total_views:,}")
            
            with cols[1]:
                total_users = ga4_data['activeusers'].sum() if has_users else 0
                display_metric("Total Users", total_users, "vs previous period", f"{total_users:,}")
            
            with cols[2]:
                avg_ctr = (total_users / total_views * 100) if has_views and has_users and total_views > 0 else 0
                display_metric("Engagement Rate", avg_ctr, "", f"{avg_ctr:.1f}%")

            if 'date' in ga4_data.columns and has_views:
                st.subheader("Traffic Trends")
                ga4_data['date'] = pd.to_datetime(ga4_data['date'])
                ga4_data = ga4_data.sort_values('date')
                
                fig = px.line(ga4_data, x='date', y='screenpageviews',
                             title="Daily Page Views",
                             labels={'screenpageviews': 'Page Views', 'date': 'Date'})
                st.plotly_chart(fig, use_container_width=True)

    with st.expander("🌐 Domain Authority", expanded=True):
        if seo_data is None:
            st.warning("No SEO metrics data available")
        else:
            # Display authority metrics
            has_da = 'domainauthority' in seo_data.columns
            has_links = 'backlinks' in seo_data.columns
            
            cols = st.columns(3)
            with cols[0]:
                if has_da:
                    da_score = seo_data['domainauthority'].iloc[0]
                    display_metric("Domain Authority", da_score, "", f"{da_score:.0f}/100")
            
            with cols[1]:
                if has_links:
                    backlinks = seo_data['backlinks'].iloc[0]
                    display_metric("Total Backlinks", backlinks, "", f"{backlinks:,}")
            
            with cols[2]:
                if 'spamscore' in seo_data.columns:
                    spam_score = seo_data['spamscore'].iloc[0]
                    display_metric("Spam Score", spam_score, "", f"{spam_score:.0f}/100")

            if all(col in seo_data.columns for col in ['keyword', 'position']):
                st.subheader("Keyword Rankings")
                
                # Create ranking distribution
                ranking_bins = [0, 3, 10, 20, 50, 100, float('inf')]
                ranking_labels = ["1-3", "4-10", "11-20", "21-50", "51-100", "100+"]
                
                ranked_keywords = seo_data.copy()
                ranked_keywords['ranking_group'] = pd.cut(
                    ranked_keywords['position'],
                    bins=ranking_bins,
                    labels=ranking_labels
                )
                
                rank_dist = ranked_keywords['ranking_group'].value_counts().sort_index().reset_index()
                rank_dist.columns = ['Position Range', 'Count']
                
                fig = px.bar(rank_dist, x='Position Range', y='Count',
                            title='Keyword Ranking Distribution',
                            color='Position Range',
                            color_discrete_sequence=px.colors.sequential.Viridis)
                st.plotly_chart(fig, use_container_width=True)

    # Add debug information in expander
    with st.expander("🔧 Debug Information", expanded=False):
        st.subheader("Data Preview")
        tab1, tab2, tab3 = st.tabs(["Search Console", "GA4", "SEO Data"])
        
        with tab1:
            st.write("Search Console Data Structure:")
            st.json(search_console_data.columns.tolist() if search_console_data is not None else [])
            if search_console_data is not None:
                st.dataframe(search_console_data.head(3))
        
        with tab2:
            st.write("GA4 Data Structure:")
            st.json(ga4_data.columns.tolist() if ga4_data is not None else [])
            if ga4_data is not None:
                st.dataframe(ga4_data.head(3))
        
        with tab3:
            st.write("SEO Data Structure:")
            st.json(seo_data.columns.tolist() if seo_data is not None else [])
            if seo_data is not None:
                st.dataframe(seo_data.head(3))