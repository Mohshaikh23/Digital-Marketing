from fastapi import FastAPI
import uvicorn

# Mock DeepSeek API
app = FastAPI()

@app.post("/v1/chat")
def deepseek_insights(data: dict):
    query = data.get("query", "")
    user_data = data.get("data", {})

    # Simulate AI insights based on the query and data
    if "traffic" in query.lower():
        response = "Your user traffic has increased by 15% over the last 30 days. Focus on organic search and paid campaigns."
    elif "conversion" in query.lower():
        response = "Your conversion rate is 5%. Optimize your landing pages and run A/B tests on CTAs."
    elif "demographics" in query.lower():
        response = "Most of your users are aged 25-34. Tailor your campaigns to this demographic."
    else:
        response = "Here are some general insights: Focus on improving user engagement and retention."

    return {"response": response}

# Run the mock API locally
def run_mock_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Uncomment the line below to run the mock API
run_mock_api()