#!/usr/bin/env python3
"""
Fetch All Users Who HAVE Reported - Extract userId, Score, Status and Save to JSON
"""

import os
import requests
import json
from datetime import datetime
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

# Planning Period IDs (from previous query)
DAILY_PLANNING_PERIOD = "43246170-b1ef-4e88-92bc-fc596d2dd2ae"
WEEKLY_PLANNING_PERIOD = "c062c8d0-3715-48e6-8e4b-af313bbfe49c"
MONTHLY_PLANNING_PERIOD = "babae54e-9678-4c75-9235-6ba4d45f6309"

# Session ID
SESSION_ID = "8473a9ad-f77c-40c9-91b9-ce5d087adf48"

def main():
    if not FIREBASE_ID_TOKEN:
        print("❌ No Firebase token found in .env")
        return
    
    # Build URL for submitted reports (using Daily planning period)
    url = f"{BASE_URL}/okr-report/by-planning-period/{DAILY_PLANNING_PERIOD}"
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": TENANT_ID,
        "Content-Type": "application/json"
    }
    
    # Request body - get all users who HAVE reported
    body = {
        "userIds": ["all"],
        "sessionIds": ["all"]
    }
    
    # Query parameters for pagination - fetch all users
    params = {
        "page": 1,
        "limit": 1000  # High limit to get all users
    }
    
    print(f"🔍 Fetching reports from: {url}")
    print(f"📋 Planning Period: Daily")
    print(f"📦 Fetching all users...\n")
    
    # Make POST request
    response = requests.post(
        url, 
        headers=headers,
        json=body,
        params=params,
        timeout=15, 
        verify=False
    )
    
    print(f"📊 Status Code: {response.status_code}\n")
    
    if response.status_code in [200, 201]:
        data = response.json()
        
        # Extract only userId, reportScore, and status
        all_reports = []
        for report in data.get("items", []):
            all_reports.append({
                "userId": report.get("userId"),
                "reportScore": report.get("reportScore"),
                "status": report.get("status"),
                "createdAt": report.get("createdAt")
            })
        
        # Filter by December 30 and 31, 2025
        filtered_reports = []
        for report in all_reports:
            created_at = report.get("createdAt")
            if created_at:
                # Parse the ISO date string
                report_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                # Check if date is December 30 or 31, 2025
                if report_date.year == 2025 and report_date.month == 12 and report_date.day in [30, 31]:
                    filtered_reports.append(report)
        
        # Create summary
        summary = {
            "totalReports": len(all_reports),
            "filteredReports": len(filtered_reports),
            "filterCriteria": "December 30-31, 2025",
            "planningPeriod": "Daily",
            "fetchedAt": datetime.now().isoformat(),
            "reports": filtered_reports
        }
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Saved {len(filtered_reports)} reports to {filename}")
        print(f"\n📊 Summary:")
        print(f"   Total Reports (All): {len(all_reports)}")
        print(f"   Filtered Reports (Dec 30-31): {len(filtered_reports)}")
        print(f"\n🔍 Sample (first 5 users on Dec 30-31):")
        for report in filtered_reports[:5]:
            print(f"   - User: {report['userId']}")
            print(f"     Score: {report['reportScore']}, Status: {report['status']}")
            print(f"     Reported at: {report['createdAt']}\n")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    main()