#!/usr/bin/env python3
"""
Fetch Parent Hierarchy Data from Planning Periods API
Fetches, decrypts, and saves the direct backend response
"""

import os
import sys
import requests
import json
from datetime import datetime, date
from dotenv import load_dotenv
import urllib3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

BASE_URL = "https://ie-okr-backend.selamnew.com/api/v1"
FIREBASE_ID_TOKEN = os.getenv("FIREBASE_API_KEY")
TENANT_ID = os.getenv("TENANT_ID", "9b320d7d-bece-4dd4-bb87-dd226f70daef")

# Planning Periods
DAILY_PLANNING_PERIOD = "43246170-b1ef-4e88-92bc-fc596d2dd2ae"
WEEKLY_PLANNING_PERIOD = "c062c8d0-3715-48e6-8e4b-af313bbfe49c"
MONTHLY_PLANNING_PERIOD = "babae54e-9678-4c75-9235-6ba4d45f6309"

# Use Daily by default (change as needed)
PLANNING_PERIOD = DAILY_PLANNING_PERIOD

USER_ID = "58d3a94c-aede-4319-a81f-99880305ff3e"

# Encryption keys
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT", "default-salt")
ENCRYPTION_IV = os.getenv("ENCRYPTION_IV")


def derive_key(password: str, salt_hex: str) -> bytes:
    """Derive encryption key using PBKDF2."""
    salt_bytes = bytes.fromhex(salt_hex)
    salt_string = salt_bytes.decode('utf-8', errors='replace')
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt_string.encode('utf-8'),
        iterations=1000,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def decrypt_response(encrypted_text: str) -> dict:
    """Decrypt encrypted backend response."""
    if not ENCRYPTION_KEY or not ENCRYPTION_IV:
        raise Exception("Encryption keys not found in .env")
    
    parts = encrypted_text.split(':')
    if len(parts) != 2:
        raise ValueError("Invalid encrypted format")
    
    iv_hex, encrypted_data_with_tag = parts
    iv = bytes.fromhex(iv_hex)
    encrypted_bytes = bytes.fromhex(encrypted_data_with_tag)
    
    key = derive_key(ENCRYPTION_KEY, ENCRYPTION_SALT)
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(iv, encrypted_bytes, None)
    
    return json.loads(decrypted.decode('utf-8'))


def filter_plans_by_date(data: dict, target_date: str = None) -> dict:

    if target_date is None:
        target_date = date.today().isoformat()
    
    if not isinstance(data, dict) or 'planData' not in data:
        return data
    
    filtered_plans = []
    
    for plan in data['planData']:
        # Check if any task in this plan was created on target date
        has_target_date_task = False
        filtered_tasks = []
        
        if 'tasks' in plan and isinstance(plan['tasks'], list):
            for task in plan['tasks']:
                if 'createdAt' in task:
                    # Extract date from ISO timestamp
                    task_date = task['createdAt'].split('T')[0]
                    if task_date == target_date:
                        has_target_date_task = True
                        filtered_tasks.append(task)
        
        # If plan has tasks from target date, include it with only those tasks
        if has_target_date_task:
            filtered_plan = plan.copy()
            filtered_plan['tasks'] = filtered_tasks
            filtered_plans.append(filtered_plan)
    
    # Create filtered response
    filtered_data = data.copy()
    filtered_data['planData'] = filtered_plans
    
    return filtered_data


def main():
    if not FIREBASE_ID_TOKEN:
        print("❌ No Firebase token found")
        return
    
    # Parse command-line arguments for date filtering
    filter_date = None
    if len(sys.argv) > 1:
        filter_date = sys.argv[1]
        try:
            # Validate date format
            datetime.strptime(filter_date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Invalid date format: {filter_date}")
            print("Usage: python okr.py [YYYY-MM-DD]")
            print("Example: python okr.py 2026-01-01")
            return
    else:
        filter_date = date.today().isoformat()
    
    # Fetch parent hierarchy data for the planning period
    url = f"{BASE_URL}/planning-periods/parent-hierarchy/{PLANNING_PERIOD}/user/{USER_ID}"
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": TENANT_ID,
        "Content-Type": "application/json"
    }
    
    period_name = "Weekly" if PLANNING_PERIOD == WEEKLY_PLANNING_PERIOD else ("Daily" if PLANNING_PERIOD == DAILY_PLANNING_PERIOD else "Monthly")
    print(f"🔍 Fetching Parent Hierarchy Data - {period_name}")
    print(f"API: {url}")
    print(f"User: {USER_ID}")
    print(f"📅 Filter Date: {filter_date}\n")
    
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    
    print(f"Status: {response.status_code}\n")
    
    if response.status_code in [200, 201]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Parse response
            response_data = response.json()
            
            # Save raw backend response first
            raw_response_filename = f"parent_hierarchy_raw_response_{timestamp}.json"
            with open(raw_response_filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Raw backend response saved: {raw_response_filename}\n")
            
            # Check if encrypted
            if isinstance(response_data, dict) and 'data' in response_data and isinstance(response_data['data'], str):
                print("🔐 Response is encrypted, decrypting...\n")
                
                # Decrypt
                decrypted_data = decrypt_response(response_data['data'])
                
                # Save full decrypted version
                decrypted_filename = f"parent_hierarchy_decrypted_{timestamp}.json"
                with open(decrypted_filename, 'w', encoding='utf-8') as f:
                    json.dump(decrypted_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Full decrypted saved: {decrypted_filename}")
                
                # Filter for specified date's plans
                filtered_data = filter_plans_by_date(decrypted_data, filter_date)
                
                # Save filtered data with date in filename
                date_label = filter_date.replace('-', '')
                filtered_filename = f"parent_hierarchy_filtered_{date_label}_{timestamp}.json"
                with open(filtered_filename, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Filtered data ({filter_date}) saved: {filtered_filename}\n")
                
                # Show summary
                if isinstance(decrypted_data, dict):
                    print(f"✅ Parent hierarchy data fetched successfully")
                    print(f"📊 Data keys: {list(decrypted_data.keys())}")
                    
                    # Show counts
                    if 'planData' in decrypted_data:
                        all_plans = decrypted_data.get('planData', [])
                        filtered_plans = filtered_data.get('planData', []) if isinstance(filtered_data, dict) else []
                        
                        # Count total tasks
                        all_tasks = sum(len(plan.get('tasks', [])) for plan in all_plans)
                        filtered_tasks = sum(len(plan.get('tasks', [])) for plan in filtered_plans)
                        
                        print(f"✅ Total plans: {len(all_plans)} (Total tasks: {all_tasks})")
                        print(f"📅 Filtered plans ({filter_date}): {len(filtered_plans)} (Filtered tasks: {filtered_tasks})")
                    
                    print(f"\n✅ All backend data saved to files (see above)")
                else:
                    print(f"✅ Parent hierarchy data fetched and decrypted")
            else:
                # Not encrypted, already saved as raw response above
                print(f"✅ Response not encrypted")
                print(f"💾 Full data saved: {raw_response_filename}")
                
                # Filter for specified date's plans
                filtered_data = filter_plans_by_date(response_data, filter_date)
                
                # Save filtered data with date in filename
                date_label = filter_date.replace('-', '')
                filtered_filename = f"parent_hierarchy_filtered_{date_label}_{timestamp}.json"
                with open(filtered_filename, 'w', encoding='utf-8') as f:
                    json.dump(filtered_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Filtered data ({filter_date}) saved: {filtered_filename}\n")
                
                # Show summary
                if isinstance(response_data, dict):
                    print(f"📊 Data keys: {list(response_data.keys())}")
                    
                    # Show counts
                    if 'planData' in response_data:
                        all_plans = response_data.get('planData', [])
                        filtered_plans = filtered_data.get('planData', []) if isinstance(filtered_data, dict) else []
                        
                        # Count total tasks
                        all_tasks = sum(len(plan.get('tasks', [])) for plan in all_plans)
                        filtered_tasks = sum(len(plan.get('tasks', [])) for plan in filtered_plans)
                        
                        print(f"✅ Total plans: {len(all_plans)} (Total tasks: {all_tasks})")
                        print(f"📅 Filtered plans ({filter_date}): {len(filtered_plans)} (Filtered tasks: {filtered_tasks})")
                
        except json.JSONDecodeError:
            print("❌ Error parsing JSON")
            print("RAW RESPONSE:")
            print(response.text)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            # Save error response to file for debugging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = f"error_response_{timestamp}.txt"
            with open(error_file, 'w') as f:
                f.write(response.text)
            print(f"💾 Error response saved to: {error_file}")
    else:
        print(f"❌ API ERROR: Status {response.status_code}")
        # Save error response to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        error_file = f"api_error_{timestamp}.txt"
        with open(error_file, 'w') as f:
            f.write(f"Status: {response.status_code}\n")
            f.write(f"Response: {response.text}")
        print(f"💾 Error saved to: {error_file}")

if __name__ == "__main__":
    main()
