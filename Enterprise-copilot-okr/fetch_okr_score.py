#!/usr/bin/env python3
"""
Fetch User OKR Score - Calculate user's OKR score
"""

import os
import requests
import json
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "https://test-okr-backend.ienetworks.co/api/v1"
USER_ID = "763bb754-8c6e-405d-b235-33e74ce485b5"

FIREBASE_ID_TOKEN = os.getenv("FIREBASE_API_KEY")
TENANT_ID = os.getenv("TENANT_ID", "9b320d7d-bece-4dd4-bb87-dd226f70daef")

def main():
    if not FIREBASE_ID_TOKEN:
        print("❌ No Firebase token found in .env")
        return
    
    # Build URL for user OKR score calculation
    url = f"{BASE_URL}/objective/user/{USER_ID}"
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": TENANT_ID,
        "Content-Type": "application/json"
    }
    
    # Make GET request
    response = requests.get(
        url, 
        headers=headers,
        params={"page": 1, "limit": 10},
        timeout=15, 
        verify=False
    )
    
    # Print the complete backend response
    print(response.text)

if __name__ == "__main__":
    main()