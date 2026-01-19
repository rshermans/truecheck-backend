import requests
import json

# Admin token - you'll need to replace this with a valid admin token
# Get it by logging in as admin and copying from localStorage
TOKEN = input("Enter admin token (from browser localStorage 'truecheck_token'): ")

url = "http://localhost:5000/api/news/update"
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

print("Updating news feed...")
response = requests.post(url, headers=headers)

if response.status_code == 200:
    print("✅ Success!")
    print(response.json())
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
