import streamlit as st
import pandas as pd
import requests
import json

def page_deepseek_ai(user_traffic_data, conversion_data, demographics_data, 
                    device_data, events_data, ecommerce_data, ltv_data, 
                    audience_data, app_data, funnel_data, retention_data, 
                    site_speed_data, error_data):
    st.title("🤖 AI Insights")
    st.markdown("Advanced insights and recommendations from our AI marketing expert")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.header("💬 Ask the Marketing AI")
    user_input = st.text_input("Ask a question about your marketing performance:")

    if user_input:
        # Prepare data payload for AI
        data_payload = {
            "query": user_input,
            "data_sources": {
                "has_user_traffic": not user_traffic_data.empty if user_traffic_data is not None else False,
                "has_conversion": not conversion_data.empty if conversion_data is not None else False,
                "has_demographics": not demographics_data.empty if demographics_data is not None else False,
                "has_ecommerce": not ecommerce_data.empty if ecommerce_data is not None else False
            }
        }

        # Simulate AI response (in a real app, this would call an API)
        ai_response = simulate_ai_response(user_input, data_payload)
        
        # Add to chat history
        st.session_state.chat_history.append({
            "user": user_input,
            "ai": ai_response
        })

    st.header("📝 Conversation History")
    for chat in st.session_state.chat_history:
        st.markdown(f"**You:** {chat['user']}")
        st.markdown(f"**AI:** {chat['ai']}")
        st.markdown("---")

    st.header("🔍 Automated Insights")
    if st.button("Generate Marketing Insights"):
        insights = generate_automated_insights(
            user_traffic_data, conversion_data, demographics_data,
            ecommerce_data, events_data
        )
        st.markdown(insights)

def simulate_ai_response(query, data_payload):
    """Simulate an AI response based on query and available data"""
    if "traffic" in query.lower():
        return "Your traffic data shows healthy growth. Consider focusing on converting more of your visitors through targeted CTAs."
    elif "conversion" in query.lower():
        return "Conversion rates could be improved. Try A/B testing your landing pages to optimize for better performance."
    else:
        return "Based on your marketing data, I recommend focusing on improving engagement through more personalized content."

def generate_automated_insights(*data_sources):
    """Generate automated insights from available data"""
    insights = []
    
    # Traffic insights
    if data_sources[0] is not None and not data_sources[0].empty:
        insights.append("🚀 **Traffic Insights**: Your website traffic shows consistent growth week-over-week.")
    
    # Conversion insights
    if data_sources[1] is not None and not data_sources[1].empty:
        insights.append("💰 **Conversion Insights**: Conversion rates are stable but could benefit from optimization.")
    
    # Demographic insights
    if data_sources[2] is not None and not data_sources[2].empty:
        insights.append("🌍 **Demographic Insights**: Your primary audience is coming from North America and Europe.")
    
    # E-commerce insights
    if data_sources[3] is not None and not data_sources[3].empty:
        insights.append("🛒 **E-commerce Insights**: Your top-selling products are driving most of your revenue.")
    
    return "\n\n".join(insights) if insights else "No significant insights could be generated from the available data."