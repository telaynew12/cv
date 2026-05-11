#!/usr/bin/env python3
"""
Direct Backend Response: Who Has NOT Closed/Validated Plans
"""

import os
import requests
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "https://test-okr-backend.ienetworks.co/api/v1"
FIREBASE_ID_TOKEN = os.getenv("FIREBASE_API_KEY")
TENANT_ID = os.getenv("TENANT_ID", "9b320d7d-bece-4dd4-bb87-dd226f70daef")

# Planning Period IDs
DAILY_PLANNING_PERIOD = "43246170-b1ef-4e88-92bc-fc596d2dd2ae"

def main():
    if not FIREBASE_ID_TOKEN:
        print("❌ No Firebase token found in .env")
        return
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": TENANT_ID,
        "Content-Type": "application/json"
    }
    
    # Fetch direct backend response
    url = f"{BASE_URL}/okr-report/by-planning-period/{DAILY_PLANNING_PERIOD}"
    body = {"userIds": ["all"], "sessionIds": ["all"]}
    params = {"page": 1, "limit": 10}  # Limit to 10 for readable output
    
    print(f"🔍 Testing: {url}")
    print(f"📋 Body: {body}")
    print(f"📦 Params: {params}\n")
    
    response = requests.post(
        url,
        headers=headers,
        json=body,
        params=params,
        timeout=15,
        verify=False
    )
    
    print(f"📊 Status Code: {response.status_code}\n")
    print("=" * 80)
    print("DIRECT BACKEND RESPONSE:")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    
    # Also show key validation fields clearly
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"\n📋 Validation Status Summary (first 10 items):\n")
        
        for idx, item in enumerate(data.get("items", [])[:10], 1):
            plan = item.get("plan", {})
            print(f"{idx}. User: {item.get('userId')}")
            print(f"   Plan ID: {plan.get('id')}")
            print(f"   ✅ isValidated (Plan Closed): {plan.get('isValidated', False)}")
            print(f"   ✅ isReportValidated (Report Closed): {plan.get('isReportValidated', False)}")
            print(f"   📝 isReported (User Submitted): {plan.get('isReported', False)}")
            print(f"   Score: {item.get('reportScore')}")
            print()

if __name__ == "__main__":
    main()
