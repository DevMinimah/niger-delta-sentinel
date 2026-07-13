import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Copernicus Authentication URL
url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# Payload for the API
payload = {
    "grant_type": "password",
    "client_id": "cdse-public",
    "username": os.getenv("CDSE_USERNAME"),
    "password": os.getenv("CDSE_PASSWORD")
}

try:
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("✅ SUCCESS! You are connected to Copernicus.")
    else:
        print(f"❌ FAILED. Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"❌ SCRIPT ERROR: {e}")