#!/usr/bin/env python3
"""
Fetch Weekly Plans from Backend API
Fetches weekly plans from GET /plan endpoint using session ID
Filters by date (default: today)
Filters plans where at least one of isValidated, isReportValidated, or isReported is false
"""

import os
import requests
import json
import urllib3
from datetime import datetime, date, timedelta
import concurrent.futures
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

# Import configuration from config.py
from config import (
    BASE_URL,
    ORG_AND_EMP_URL,
    FIREBASE_ID_TOKEN,
    TENANT_ID,
    SESSION_ID,
    REQUEST_TIMEOUT,
    MAX_WORKERS,
    PORT,
    HOST
)

# Import decryption from decrypt.py
from decrypt import AesGcmDecryptor, decrypt_if_encrypted, is_encrypted, DecryptionError, InvalidEnvelopeError

# Import encryption config for legacy fallback
from config import ENCRYPTION_KEY, ENCRYPTION_SALT, ENCRYPTION_IV

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize decryptor from decrypt.py
# decrypt.py will use RAW_AES_KEY_HEX or ENCRYPTION_KEY + ENCRYPTION_SALT from .env
decryptor = None
try:
    from config import RAW_AES_KEY_HEX
    if RAW_AES_KEY_HEX:
        decryptor = AesGcmDecryptor(RAW_AES_KEY_HEX)
except Exception:
    # Will use legacy decrypt_if_encrypted which uses module-level key from decrypt.py
    pass


def decrypt_response_data(response_data):
    """
    Decrypt response data using decrypt.py, with fallback to legacy format if needed.
    Handles both new format (enc:v1:...) and legacy format (iv:data).
    Returns the decrypted data, or original data if not encrypted.
    """
    # If response_data is already a list (not encrypted), return as-is
    if isinstance(response_data, list):
        return response_data
    
    # If response_data is a dict with 'data' field
    if isinstance(response_data, dict) and 'data' in response_data:
        encrypted_text = response_data['data']
        
        # If data is not a string, it's already decrypted
        if not isinstance(encrypted_text, str):
            return encrypted_text
        
        # Check if it's encrypted (new format: enc:v1:...)
        if is_encrypted(encrypted_text):
            # Use decrypt.py for new format
            try:
                if decryptor:
                    return decryptor.decrypt_response(encrypted_text)
                else:
                    # Use module-level decrypt_if_encrypted
                    return decrypt_if_encrypted(response_data)
            except (InvalidEnvelopeError, DecryptionError, ValueError) as e:
                print(f"   ⚠️  New format decryption failed: {str(e)}")
                raise
        
        # Check if it's legacy format (iv_hex:encrypted_data_with_tag)
        elif ':' in encrypted_text and len(encrypted_text.split(':')) == 2:
            # Legacy format: iv_hex:encrypted_data_with_tag
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.backends import default_backend
                
                if not ENCRYPTION_KEY:
                    raise ValueError("Legacy decryption requires ENCRYPTION_KEY")
                
                parts = encrypted_text.split(':')
                if len(parts) != 2:
                    raise ValueError("Invalid legacy encrypted format")
                
                iv_hex, encrypted_data_with_tag = parts
                
                # Derive key using PBKDF2HMAC (legacy method)
                salt_bytes = bytes.fromhex(ENCRYPTION_SALT) if ENCRYPTION_SALT else b'default-salt'
                salt_string = salt_bytes.decode('utf-8', errors='replace')
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt_string.encode('utf-8'),
                    iterations=1000,
                    backend=default_backend()
                )
                key = kdf.derive(ENCRYPTION_KEY.encode('utf-8'))
                
                # Decrypt
                aesgcm = AESGCM(key)
                decrypted = aesgcm.decrypt(bytes.fromhex(iv_hex), bytes.fromhex(encrypted_data_with_tag), None)
                decrypted_data = json.loads(decrypted.decode('utf-8'))
                
                return decrypted_data
            except Exception as e:
                print(f"   ⚠️  Legacy decryption failed: {str(e)}")
                raise
        
        # If data is a string but not encrypted, return as-is (might be JSON string)
        else:
            try:
                # Try to parse as JSON
                return json.loads(encrypted_text)
            except:
                # If not JSON, return original response_data
                return response_data
    
    # If response_data is a dict without 'data' field, try decrypt_if_encrypted
    if isinstance(response_data, dict):
        try:
            return decrypt_if_encrypted(response_data)
        except (InvalidEnvelopeError, DecryptionError, ValueError):
            # Not encrypted, return as-is
            return response_data
    
    # Return as-is if not recognized format
    return response_data


def parse_date(date_str):
    """Parse date string to date object"""
    if isinstance(date_str, str):
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.date()
        except:
            try:
                return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
            except:
                return None
    return None


def extract_items(data):
    """Extract items array from various response structures"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if 'items' in data:
            return data.get('items', [])
        if 'data' in data:
            return extract_items(data['data'])
    return []


def fetch_all_users_once(tenant_id=None):
    """Fetch all users once and return as a dictionary for fast lookup"""
    error_info = None
    if not FIREBASE_ID_TOKEN:
        error_msg = "No Firebase token for users API"
        print(f"   ❌ {error_msg}")
        return {}, error_msg
    
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": tenant_id or TENANT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # Debug: Show what base URL we're using
        print(f"   🔍 Base URL: {ORG_AND_EMP_URL}")
        
        # Try multiple endpoints as fallback
        endpoints_to_try = [
            f"{ORG_AND_EMP_URL}/users",  # Try this first
            f"{ORG_AND_EMP_URL}/users/all-users/all",  # Fallback to this
        ]
        
        # Debug: Show all URLs we'll try
        print(f"   🔍 Will try {len(endpoints_to_try)} endpoints:")
        for idx, ep in enumerate(endpoints_to_try, 1):
            print(f"      {idx}. {ep}")
        
        response = None
        errors_tried = []
        
        for users_endpoint in endpoints_to_try:
            print(f"   📡 Trying {users_endpoint}...")
            try:
                response = requests.get(users_endpoint, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
                print(f"   📊 Users API Status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    print(f"   ✅ Success with {users_endpoint}")
                    break  # Success, exit loop
                elif response.status_code == 404:
                    # Try next endpoint
                    error_info = f"{users_endpoint} -> 404 Not Found"
                    errors_tried.append(error_info)
                    print(f"   ⚠️  {error_info}, trying next endpoint...")
                    response = None  # Reset response so we try next
                    continue
                else:
                    # Other error, but endpoint exists (like 400, 401, 403, 500)
                    error_text = ""
                    try:
                        error_text = response.text[:500]
                    except:
                        pass
                    error_info = f"{users_endpoint} -> {response.status_code}: {error_text}"
                    errors_tried.append(error_info)
                    print(f"   ❌ {error_info}")
                    # For non-404 errors, we might want to stop or continue depending on error
                    # If it's 400 (bad request), the endpoint exists but request is wrong
                    # If it's 401/403, authentication issue
                    if response.status_code in [400, 401, 403]:
                        # Endpoint exists but has issues, don't try others
                        break
                    # For 500+ errors, might be temporary, could try next endpoint
                    continue
            except Exception as e:
                error_info = f"{users_endpoint} -> Exception: {str(e)}"
                errors_tried.append(error_info)
                print(f"   ⚠️  {error_info}, trying next endpoint...")
                response = None
                continue
        
        if not response or response.status_code not in [200, 201]:
            error_msg = f"All endpoints failed. Tried: {'; '.join(errors_tried)}"
            print(f"   ❌ {error_msg}")
            return {}, error_msg
        
        response_data = response.json()
        # Use decrypt.py for decryption (with legacy fallback)
        print(f"   🔓 Decrypting users data...")
        try:
            data = decrypt_response_data(response_data)
        except Exception as e:
            error_msg = f"Failed to decrypt users data: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {}, error_msg
        
        items = extract_items(data)
        print(f"   📋 Extracted {len(items)} user items")
        
        # Create a dictionary for O(1) lookup
        users_dict = {item.get('id'): item for item in items if isinstance(item, dict) and item.get('id')}
        print(f"   ✅ Created users_dict with {len(users_dict)} users")
        
        # Show sample user structure
        if users_dict:
            sample_user = list(users_dict.values())[0]
            print(f"   🔍 Sample user keys: {list(sample_user.keys())[:10]}")
        
        return users_dict, None
    except Exception as e:
        error_msg = f"Exception in fetch_all_users_once: {str(e)}"
        print(f"   ❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return {}, error_msg


def fetch_supervisor_info_optimized(user_id, users_dict, tenant_id=None, debug=False):
    """Fetch supervisor information using cached users dictionary"""
    if not FIREBASE_ID_TOKEN or not user_id:
        if debug:
            print(f"      ❌ Missing token or user_id for {user_id}")
        return None
    
    if not users_dict:
        if debug:
            print(f"      ❌ users_dict is empty for {user_id}")
        return None
    
    # FIRST: Try to get supervisor directly from user's reportingTo field (fastest, no API call)
    user_details = users_dict.get(user_id)
    if user_details and isinstance(user_details, dict):
        reporting_to = user_details.get('reportingTo')
        if reporting_to and isinstance(reporting_to, dict):
            # Direct supervisor info from reportingTo object
            return {
                "id": reporting_to.get('id'),
                "firstName": reporting_to.get('firstName'),
                "middleName": reporting_to.get('middleName'),
                "lastName": reporting_to.get('lastName')
            }
        # If reportingTo is just an ID, look it up
        elif reporting_to and isinstance(reporting_to, str):
            supervisor_details = users_dict.get(reporting_to)
            if supervisor_details and isinstance(supervisor_details, dict):
                return {
                    "id": supervisor_details.get('id'),
                    "firstName": supervisor_details.get('firstName'),
                    "middleName": supervisor_details.get('middleName'),
                    "lastName": supervisor_details.get('lastName')
                }
    
    # SECOND: Fallback to dashboard API to get supervisorId
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": tenant_id or TENANT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # Get user dashboard data which includes supervisorId
        url = f"{BASE_URL}/okr-total-summary/user/dashboard/{user_id}"
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        if response.status_code not in [200, 201]:
            if debug:
                print(f"      ❌ Dashboard API failed for {user_id}: Status {response.status_code}")
            return None
        
        response_data = response.json()
        # Use decrypt.py for decryption (with legacy fallback)
        try:
            data = decrypt_response_data(response_data)
        except Exception as e:
            if debug:
                print(f"      ❌ Decryption failed for {user_id}: {str(e)}")
            return None
        
        supervisor_id = data.get('supervisorId') if isinstance(data, dict) else None
        if not supervisor_id:
            if debug:
                print(f"      ⚠️  No supervisorId in dashboard for {user_id}")
            return None
        
        # Use cached users dictionary instead of API call
        supervisor_details = users_dict.get(supervisor_id)
        if supervisor_details and isinstance(supervisor_details, dict):
            return {
                "id": supervisor_details.get('id'),
                "firstName": supervisor_details.get('firstName'),
                "middleName": supervisor_details.get('middleName'),
                "lastName": supervisor_details.get('lastName')
            }
        else:
            if debug:
                print(f"      ⚠️  Supervisor {supervisor_id} not found in users_dict")
    except Exception as e:
        if debug:
            print(f"      ❌ Exception for {user_id}: {str(e)}")
        return None
    return None


def fetch_weekly_plans(session_id=None, start_date=None, end_date=None, save_to_file=True):
    if not FIREBASE_ID_TOKEN:
        print("❌ No Firebase token found")
        return None
    
    # Default: use today's date for both start and end if not provided
    if start_date is None and end_date is None:
        start_date = date.today()
        end_date = date.today()
    else:
        # Parse start_date
        if start_date is None:
            start_date = date.today()
        elif isinstance(start_date, str):
            start_date = parse_date(start_date) or date.today()
        elif isinstance(start_date, date):
            pass  # Already a date object
        else:
            start_date = date.today()
        
        # Parse end_date
        if end_date is None:
            end_date = start_date  # If end_date not provided, use start_date
        elif isinstance(end_date, str):
            end_date = parse_date(end_date) or start_date
        elif isinstance(end_date, date):
            pass  # Already a date object
        else:
            end_date = start_date
    
    # Ensure start_date <= end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    active_session_id = session_id or SESSION_ID
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": TENANT_ID,
        "Content-Type": "application/json"
    }
    
    if active_session_id:
        headers["sessionId"] = active_session_id
    
    url = f"{BASE_URL}/plan"
    print(f"{'='*80}\n📥 FETCHING WEEKLY PLANS\n{'='*80}")
    print(f"Endpoint: {url}\nSession ID: {active_session_id or 'Not specified'}")
    if start_date == end_date:
        print(f"Date: {start_date}\nTenant ID: {TENANT_ID}\n")
    else:
        print(f"Date Range: {start_date} to {end_date}\nTenant ID: {TENANT_ID}\n")
    
    try:
        print("   ⏳ Connecting to server...")
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        print(f"📊 Status Code: {response.status_code}\n")
        
        if response.status_code not in [200, 201]:
            print(f"❌ Error: Status {response.status_code}")
            return None
        
        response_data = response.json()
        
        # Debug: Show response structure
        print(f"   🔍 Response type: {type(response_data)}")
        if isinstance(response_data, dict):
            print(f"   🔍 Response keys: {list(response_data.keys())[:5]}")
            if 'data' in response_data:
                data_sample = str(response_data['data'])[:100] if isinstance(response_data['data'], str) else type(response_data['data'])
                print(f"   🔍 Data type: {type(response_data['data'])}, sample: {data_sample}...")
        
        # Use decrypt.py for decryption (with legacy fallback)
        print("   🔓 Decrypting...")
        try:
            data = decrypt_response_data(response_data)
            print(f"   ✅ Decrypted, data type: {type(data)}\n")
        except Exception as e:
            print(f"   ❌ Decryption error: {str(e)}\n")
            import traceback
            traceback.print_exc()
            return None
        
        # Extract plans list from data
        if isinstance(data, list):
            all_plans = data
        elif isinstance(data, dict):
            # Try to extract plans from various possible keys
            all_plans = data.get('items', data.get('data', data.get('plans', [])))
            if not isinstance(all_plans, list):
                all_plans = []
        else:
            all_plans = []
        
        print(f"📊 Total plans fetched: {len(all_plans)}\n")
        
        # Filter for weekly plans first (faster - reduces dataset early)
        weekly_plans = [plan for plan in all_plans if plan.get('description') == 'Weekly']
        print(f"📅 Found {len(weekly_plans)} weekly plans")
        if start_date == end_date:
            print(f"🔍 Filtering by date ({start_date}) and status...\n")
        else:
            print(f"🔍 Filtering by date range ({start_date} to {end_date}) and status...\n")
        
        # Filter by date and status in one pass (optimized)
        filtered_plans = []
        for plan in weekly_plans:
            # Check date first (faster check)
            plan_date = None
            for date_field in ['createdAt', 'updatedAt']:
                if date_field in plan and plan[date_field]:
                    plan_date = parse_date(plan[date_field])
                    if plan_date:
                        break
            
            # Skip if date doesn't match
            if not plan_date or not (start_date <= plan_date <= end_date):
                continue
            
            # Check status (only if date matches)
            isValidated = plan.get('isValidated', False)
            isReportValidated = plan.get('isReportValidated', False)
            isReported = plan.get('isReported', False)
            
            # Only include if at least one is false
            if not (isValidated and isReportValidated and isReported):
                filtered_plans.append(plan)
        
        # Fetch supervisor information for unique user IDs (OPTIMIZED)
        print("👔 Fetching supervisor information...")
        unique_user_ids = list(set(plan.get('userId') for plan in filtered_plans if plan.get('userId')))
        
        # Fetch all users once at the beginning
        print(f"   📥 Fetching all users (one-time)...")
        users_dict, users_error = fetch_all_users_once(TENANT_ID)
        if users_error:
            print(f"   ⚠️  Users API Error: {users_error}")
        print(f"   ✅ Loaded {len(users_dict)} users into cache")
        
        # Store error for API response
        supervisor_error = users_error
        
        # Use parallel processing for dashboard calls
        supervisor_cache = {}
        if unique_user_ids:
            print(f"   🔄 Fetching supervisor IDs for {len(unique_user_ids)} users (parallel)...")
            if not users_dict:
                print(f"   ⚠️  WARNING: users_dict is empty! Supervisor info may not be available.")
                print(f"   🔍 Checking users API...")
            else:
                print(f"   ✅ users_dict has {len(users_dict)} users")
                # Show sample user IDs from dict
                sample_ids = list(users_dict.keys())[:3]
                print(f"   🔍 Sample user IDs in dict: {[id[:8] + '...' for id in sample_ids]}")
            
            # Test first user with debug to see what's happening
            if unique_user_ids and users_dict:
                test_user = unique_user_ids[0]
                print(f"   🔍 Testing first user {test_user[:8]}... with debug:")
                test_result = fetch_supervisor_info_optimized(test_user, users_dict, TENANT_ID, debug=True)
                if test_result:
                    print(f"   ✅ Test successful! Sample: {test_result}")
                else:
                    print(f"   ❌ Test failed for first user")
            
            # Use configured max workers
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_user = {
                    executor.submit(fetch_supervisor_info_optimized, user_id, users_dict, TENANT_ID): user_id 
                    for user_id in unique_user_ids
                }
                
                completed = 0
                errors = 0
                for future in concurrent.futures.as_completed(future_to_user):
                    user_id = future_to_user[future]
                    completed += 1
                    try:
                        supervisor_info = future.result()
                        if supervisor_info:
                            supervisor_cache[user_id] = supervisor_info
                        else:
                            errors += 1
                    except Exception as e:
                        errors += 1
                        # Silently continue - some users may not have supervisors
                        pass
                    if completed % 50 == 0:
                        print(f"   ⏳ Processed {completed}/{len(unique_user_ids)} users... (found: {len(supervisor_cache)}, errors: {errors})")
            
            print(f"   📊 Summary: {len(supervisor_cache)} users with supervisors, {len(unique_user_ids) - len(supervisor_cache)} without")
        
        # Add supervisor information to each plan
        plans_with_supervisor = 0
        plans_without_supervisor = 0
        for plan in filtered_plans:
            user_id = plan.get('userId')
            if user_id:
                if user_id in supervisor_cache:
                    plan['supervisor'] = supervisor_cache[user_id]
                    plans_with_supervisor += 1
                else:
                    # Add null supervisor to show we checked
                    plan['supervisor'] = None
                    plans_without_supervisor += 1
            else:
                plan['supervisor'] = None
        
        print(f"✅ Fetched supervisor info for {len(supervisor_cache)} users")
        print(f"📋 Added supervisor info to {plans_with_supervisor} plans")
        print(f"⚠️  Plans without supervisor: {plans_without_supervisor}\n")
        
        # Debug: Show sample of supervisor_cache
        if supervisor_cache:
            sample_user = list(supervisor_cache.keys())[0]
            print(f"🔍 Sample supervisor data for user {sample_user[:8]}...: {supervisor_cache[sample_user]}\n")
        
        result = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "endpoint": url,
            "session_id": active_session_id,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "status_code": response.status_code,
            "total_weekly_plans": len(weekly_plans),
            "filtered_plans_count": len(filtered_plans),
            "supervisor_info": {
                "users_fetched": len(users_dict),
                "supervisors_found": len(supervisor_cache),
                "plans_with_supervisor": plans_with_supervisor,
                "plans_without_supervisor": plans_without_supervisor,
                "error": supervisor_error if 'supervisor_error' in locals() else None
            },
            "weekly_plans": filtered_plans
        }
        
        print(f"✅ Total weekly plans: {result['total_weekly_plans']}")
        if start_date == end_date:
            print(f"📋 Filtered weekly plans (date: {start_date}, at least one false): {result['filtered_plans_count']}\n")
        else:
            print(f"📋 Filtered weekly plans (date range: {start_date} to {end_date}, at least one false): {result['filtered_plans_count']}\n")
        
        if save_to_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_suffix = f"_{active_session_id[:8]}" if active_session_id else ""
            if start_date == end_date:
                filename = f"weekly_plans_decrypted{session_suffix}_{start_date}_{timestamp}.json"
            else:
                filename = f"weekly_plans_decrypted{session_suffix}_{start_date}_to_{end_date}_{timestamp}.json"
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_plans, f, indent=2, ensure_ascii=False)
            print(f"💾 Weekly plans saved to: {filepath}\n")
        
        if len(filtered_plans) > 0:
            print(f"📋 Weekly Plans Sample (first 5):\n")
            for idx, plan in enumerate(filtered_plans[:5], 1):
                print(f"{idx}. Plan ID: {plan.get('id', 'N/A')}")
                print(f"   User ID: {plan.get('userId', 'N/A')}")
                print(f"   Date: {plan.get('createdAt', 'N/A')}")
                print(f"   isValidated: {plan.get('isValidated', False)}")
                print(f"   isReportValidated: {plan.get('isReportValidated', False)}")
                print(f"   isReported: {plan.get('isReported', False)}")
                print()
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    session_id = "8473a9ad-f77c-40c9-91b9-ce5d087adf48"
    
    # Default: today's date (both start and end)
    # For date range: start_date="2026-01-01", end_date="2026-01-05"
    # For single date: start_date="2026-01-04" (end_date will default to same)
    # For tomorrow: start_date=date.today() + timedelta(days=1)
    result = fetch_weekly_plans(
        session_id=session_id, 
        save_to_file=True,
        start_date="2026-01-01",
        end_date="2026-01-01",)
    
    if result:
        print(f"\n✅ Successfully fetched weekly plans!")
        if result['start_date'] == result['end_date']:
            print(f"📅 Date: {result['start_date']}")
        else:
            print(f"📅 Date Range: {result['start_date']} to {result['end_date']}")
        print(f"📅 Total weekly: {result['total_weekly_plans']}")
        print(f"📋 Filtered: {result['filtered_plans_count']}")
    else:
        print(f"\n❌ Failed to fetch weekly plans")


# FastAPI Application
app = FastAPI(
    title="Weekly Plans API",
    description="API to fetch weekly plans with supervisor information",
    version="1.0.0"
)


@app.get("/api/weekly-plans")
async def get_weekly_plans(
    session_id: Optional[str] = Query(None, description="Session ID for filtering plans"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD). Defaults to today if not provided."),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD). Defaults to start_date or today if not provided."),
    save_to_file: bool = Query(False, description="Whether to save results to a file")
):
    """
    Fetch weekly plans filtered by date range and validation status.
    
    Returns plans where at least one of isValidated, isReportValidated, or isReported is false.
    Includes supervisor information for each plan.
    """
    try:
        result = fetch_weekly_plans(
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            save_to_file=save_to_file
        )
        
        if result is None:
            raise HTTPException(
                status_code=500, 
                detail="Failed to fetch weekly plans. Check server logs for details."
            )
        
        return JSONResponse(content=result)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e) if str(e) else f"Unknown error: {type(e).__name__}"
        print(f"❌ API Error: {error_msg}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error: {error_msg}. Check server console for full traceback."
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Weekly Plans API",
        "version": "1.0.0",
        "endpoints": {
            "/api/weekly-plans": "GET - Fetch weekly plans with filters",
            "/docs": "API documentation (Swagger UI)",
            "/redoc": "API documentation (ReDoc)"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI app using config from config.py
    uvicorn.run(app, host=HOST, port=PORT)


