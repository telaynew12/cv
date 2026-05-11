#!/usr/bin/env python3
"""
Fetch All Users Plans from Backend API
Fetches direct API response from GET /plan endpoint using session ID
"""

import os
import requests
import json
from dotenv import load_dotenv
import urllib3
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("BASE_URL", "https://ie-okr-backend.selamnew.com/api/v1")

FIREBASE_ID_TOKEN = os.getenv("FIREBASE_API_KEY")
TENANT_ID = os.getenv("TENANT_ID", "9b320d7d-bece-4dd4-bb87-dd226f70daef")
SESSION_ID = os.getenv("SESSION_ID")  # Optional: can be set in .env or passed as parameter

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
        raise ValueError(f"Invalid encrypted format - expected 2 parts, got {len(parts)}")
    
    iv_hex, encrypted_data_with_tag = parts
    iv = bytes.fromhex(iv_hex)
    encrypted_bytes = bytes.fromhex(encrypted_data_with_tag)
    
    key = derive_key(ENCRYPTION_KEY, ENCRYPTION_SALT)
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(iv, encrypted_bytes, None)
    
    return json.loads(decrypted.decode('utf-8'))

def fetch_all_plans(session_id=None, save_to_file=True):
    """
    Fetch all plans from the backend API using session ID
    
    Args:
        session_id: Optional session ID. If not provided, uses SESSION_ID from env or fetches all plans
        save_to_file: Whether to save the response to a JSON file
        
    Returns:
        Dictionary containing the API response
    """
    if not FIREBASE_ID_TOKEN:
        print("❌ No Firebase token found in .env")
        return None
    
    # Use provided session_id or from env
    active_session_id = session_id or SESSION_ID
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {FIREBASE_ID_TOKEN}",
        "tenantId": TENANT_ID,
        "Content-Type": "application/json"
    }
    
    # Add sessionId to headers if provided
    if active_session_id:
        headers["sessionId"] = active_session_id
    
    # Fetch direct backend response
    url = f"{BASE_URL}/plan"
    
    print(f"{'='*80}")
    print(f"📥 FETCHING ALL PLANS")
    print(f"{'='*80}")
    print(f"Endpoint: {url}")
    print(f"Session ID: {active_session_id or 'Not specified (fetching all plans)'}")
    print(f"Tenant ID: {TENANT_ID}\n")
    
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=60,
            verify=False
        )
        
        print(f"📊 Status Code: {response.status_code}\n")
        
        if response.status_code in [200, 201]:
            try:
                response_data = response.json()
                
                # Check if response is encrypted (format: {"data": "encrypted_string"})
                if isinstance(response_data, dict) and 'data' in response_data and isinstance(response_data['data'], str):
                    print("   🔓 Response is encrypted, decrypting...")
                    try:
                        data = decrypt_response(response_data['data'])
                        print("   ✅ Decrypted successfully!\n")
                    except Exception as decrypt_error:
                        print(f"   ❌ Decryption error: {decrypt_error}\n")
                        return None
                else:
                    # Response is not encrypted, use as is
                    data = response_data
                    print("   ℹ️  Response is not encrypted\n")
                
                # Prepare response structure
                result = {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": url,
                    "session_id": active_session_id,
                    "status_code": response.status_code,
                    "total_plans": len(data) if isinstance(data, list) else 0,
                    "raw_response": data
                }
                
                print(f"✅ Successfully fetched {result['total_plans']} plans\n")
                
                # Save to file if requested
                if save_to_file:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    session_suffix = f"_{active_session_id[:8]}" if active_session_id else ""
                    
                    # Save in the same directory as the script
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    
                    # Save decrypted data (clean format - just the plans array)
                    decrypted_filename = f"all_plans_decrypted{session_suffix}_{timestamp}.json"
                    decrypted_filepath = os.path.join(script_dir, decrypted_filename)
                    
                    with open(decrypted_filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    print(f"💾 Decrypted data saved to: {decrypted_filepath}")
                    
                    # Save full response with metadata
                    full_filename = f"all_plans_raw_response{session_suffix}_{timestamp}.json"
                    full_filepath = os.path.join(script_dir, full_filename)
                    
                    with open(full_filepath, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    print(f"💾 Full response with metadata saved to: {full_filepath}\n")
                
                # Display summary of first few plans
                if isinstance(data, list) and len(data) > 0:
                    print(f"📋 Sample Plans (first 5):\n")
                    for idx, plan in enumerate(data[:5], 1):
                        print(f"{idx}. Plan ID: {plan.get('id', 'N/A')}")
                        print(f"   User ID: {plan.get('userId', 'N/A')}")
                        print(f"   Session ID: {plan.get('sessionId', 'N/A')}")
                        print(f"   Description: {plan.get('description', 'N/A')}")
                        print(f"   isValidated: {plan.get('isValidated', False)}")
                        print(f"   isReported: {plan.get('isReported', False)}")
                        print()
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Response text (first 500 chars): {response.text[:500]}")
                return None
        else:
            print(f"❌ Error: API returned status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data}")
            except:
                print(f"Response: {response.text[:500]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request exception: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function to fetch all plans"""
    # Using the specified session ID
    session_id = "8473a9ad-f77c-40c9-91b9-ce5d087adf48"
    
    result = fetch_all_plans(session_id=session_id, save_to_file=True)
    
    if result:
        print(f"\n✅ Successfully fetched plans!")
        print(f"📊 Total plans: {result['total_plans']}")
    else:
        print(f"\n❌ Failed to fetch plans")


if __name__ == "__main__":
    main()
