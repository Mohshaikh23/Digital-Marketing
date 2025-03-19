import requests
import json
from urllib.parse import urlencode

# LinkedIn API credentials
CLIENT_ID = "77ndep8j4wu292"
CLIENT_SECRET = "WPL_AP1.QbWQ7871jJV6DMoB.YJhZzA=="
REDIRECT_URI = "http://localhost:8080"  # Replace with your redirect URI
ACCESS_TOKEN = "your_access_token"  # Replace with your access token

# Function to fetch LinkedIn posts
def fetch_linkedin_posts(access_token, organization_id):
    url = f"https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({organization_id})"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching LinkedIn posts: {response.status_code}, {response.text}")
        return None

# Function to fetch LinkedIn engagement metrics
def fetch_linkedin_engagement_metrics(access_token, post_id):
    url = f"https://api.linkedin.com/v2/socialActions/{post_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching engagement metrics: {response.status_code}, {response.text}")
        return None

# Main function to extract and save LinkedIn data
def extract_and_save_linkedin_data():
    organization_id = "your_organization_id"  # Replace with your LinkedIn organization ID

    # Fetch LinkedIn posts
    posts = fetch_linkedin_posts(ACCESS_TOKEN, organization_id)
    if posts:
        # Save posts to a JSON file
        with open("linkedin_posts.json", "w") as f:
            json.dump(posts, f, indent=4)
        print("LinkedIn posts saved to linkedin_posts.json")

    # Fetch engagement metrics for each post
    engagement_metrics = []
    for post in posts.get("elements", []):
        post_id = post.get("id")
        metrics = fetch_linkedin_engagement_metrics(ACCESS_TOKEN, post_id)
        if metrics:
            engagement_metrics.append(metrics)

    # Save engagement metrics to a JSON file
    with open("linkedin_engagement_metrics.json", "w") as f:
        json.dump(engagement_metrics, f, indent=4)
    print("LinkedIn engagement metrics saved to linkedin_engagement_metrics.json")

if __name__ == "__main__":
    extract_and_save_linkedin_data()