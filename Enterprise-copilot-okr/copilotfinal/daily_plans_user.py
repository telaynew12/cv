#!/usr/bin/env python3
"""
Get Someone's Daily Plans Script
Fetches someone's daily plans from OKR backend API
Endpoint: GET /plan/find-all-plans/users/:userId/planning-period/:planningPeriodId

Environment Variables (.env file):
    Required:
        ORG_AND_EMP_URL - OKR backend base URL (will auto-add /api/v1 if missing)
        TENANT_ID - Organization tenant ID
        FIREBASE_API_ID - Firebase authentication token
        REQUEST_TIMEOUT - Request timeout in seconds
        VERIFY_SSL - Enable SSL verification (true/false)
        OUTPUT_DIR - Directory to save output files
    
    Optional:
        SESSION_ID - Session ID (uses active session if not provided)
        USER_ID - User ID (can be overridden with --user-id)
        PLANNING_PERIOD_ID - Planning period ID (can be overridden with --planning-period-id)
        FOR_PLAN - forPlan query parameter (can be overridden with --for-plan)
        ENABLE_DECRYPTION - Enable response decryption (true/false)
        RAW_AES_KEY_HEX - AES-256 key in hex format (64 hex chars) for decryption
"""

import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import urllib3

# Import decryption logic
try:
    from decrypt import AesGcmDecryptor, is_encrypted, ENABLE_DECRYPTION, RAW_AES_KEY_HEX
except ImportError:
    # Fallback if decrypt.py is not available
    AesGcmDecryptor = None
    is_encrypted = lambda x: False
    ENABLE_DECRYPTION = False
    RAW_AES_KEY_HEX = None

# Import old format decryption (for legacy encrypted responses)
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
# Suppress dotenv parsing errors with better error messages
try:
    load_dotenv()
except Exception as e:
    error_msg = str(e)
    if "line" in error_msg.lower():
        print(f"⚠️  Warning: Could not parse .env file: {error_msg}")
        print("   Common issues:")
        print("   - Unquoted values with special characters")
        print("   - Missing = sign")
        print("   - Comments without # at start of line")
        print("   - Multi-line values without proper quoting")
    else:
        print(f"⚠️  Warning: Could not load .env file: {error_msg}")
    print("   Continuing with environment variables...")

# Configuration from .env
# Base URL - try multiple possible env var names
OKR_BASE_URL = os.getenv('BASE_URL_OKR')
TENANT_ID = os.getenv('TENANT_ID')
FIREBASE_TOKEN = os.getenv('FIREBASE_API_ID')
SESSION_ID = os.getenv('SESSION_ID')  # Optional

# Request configuration from .env
REQUEST_TIMEOUT_STR = os.getenv('REQUEST_TIMEOUT')
REQUEST_TIMEOUT = int(REQUEST_TIMEOUT_STR) if REQUEST_TIMEOUT_STR else None
VERIFY_SSL_STR = os.getenv('VERIFY_SSL')
VERIFY_SSL = VERIFY_SSL_STR.lower() == 'true' if VERIFY_SSL_STR else None

# Output configuration from .env
OUTPUT_DIR = os.getenv('OUTPUT_DIR')

# Optional: User ID and Planning Period ID from .env
DEFAULT_USER_ID = os.getenv('USER_ID')
DEFAULT_PLANNING_PERIOD_ID = os.getenv('PLANNING_PERIOD_ID')
DEFAULT_FOR_PLAN = os.getenv('FOR_PLAN')

# Old format encryption keys (for legacy format)
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
ENCRYPTION_SALT = os.getenv('ENCRYPTION_SALT')
ENCRYPTION_IV = os.getenv('ENCRYPTION_IV')

# Initialize decryptor if encryption is enabled
def init_decryptor():
    """Initialize decryptor if encryption is enabled"""
    if ENABLE_DECRYPTION and RAW_AES_KEY_HEX and AesGcmDecryptor:
        try:
            return AesGcmDecryptor(RAW_AES_KEY_HEX)
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize decryptor: {e}")
            return None
    return None

decryptor = init_decryptor()

def decrypt_old_format(encrypted_text: str) -> dict:
    """Decrypt old format encrypted response (iv:encrypted_data)"""
    if not CRYPTO_AVAILABLE:
        raise Exception("Cryptography library not available")
    if not ENCRYPTION_KEY:
        raise Exception("ENCRYPTION_KEY not found in .env")
    
    parts = encrypted_text.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid old format - expected 2 parts, got {len(parts)}")
    
    iv_hex, encrypted_data_with_tag = parts
    iv = bytes.fromhex(iv_hex)
    encrypted_bytes = bytes.fromhex(encrypted_data_with_tag)
    
    # Derive key using PBKDF2 (old format)
    salt_hex = ENCRYPTION_SALT or "default-salt"
    salt_bytes = bytes.fromhex(salt_hex) if len(salt_hex) % 2 == 0 else salt_hex.encode('utf-8')
    salt_string = salt_bytes.decode('utf-8', errors='replace') if isinstance(salt_bytes, bytes) else salt_hex
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt_string.encode('utf-8'),
        iterations=1000,
        backend=default_backend()
    )
    key = kdf.derive(ENCRYPTION_KEY.encode('utf-8'))
    
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(iv, encrypted_bytes, None)
    
    return json.loads(decrypted.decode('utf-8'))

def get_someone_daily_plans(user_id, planning_period_id, for_plan=None, session_id=None):
    """
    Get someone's daily plans
    
    Args:
        user_id: Target user ID
        planning_period_id: Daily planning period ID
        for_plan: Optional query parameter
        session_id: Optional session ID (uses SESSION_ID from env if not provided)
    
    Returns:
        dict: Response data or error information
    """
    # Validate required environment variables
    if not OKR_BASE_URL:
        print("❌ Error: ORG_AND_EMP_URL not found in .env file")
        print("\n📝 Please add to your .env file:")
        print("   ORG_AND_EMP_URL=https://your-okr-backend.com/api/v1")
        print("   (or just the domain, script will add /api/v1 automatically)")
        sys.exit(1)
    
    if not TENANT_ID:
        print("❌ Error: TENANT_ID not found in .env file")
        print("\n📝 Please add to your .env file:")
        print("   TENANT_ID=your-tenant-id")
        sys.exit(1)
    
    if not FIREBASE_TOKEN:
        print("❌ Error: FIREBASE_API_ID not found in .env file")
        print("\n📝 Please add to your .env file:")
        print("   FIREBASE_API_ID=your-firebase-token")
        sys.exit(1)
    
    if REQUEST_TIMEOUT is None:
        print("❌ Error: REQUEST_TIMEOUT not found in .env file")
        print("\n📝 Please add to your .env file:")
        print("   REQUEST_TIMEOUT=30")
        sys.exit(1)
    
    if VERIFY_SSL is None:
        print("❌ Error: VERIFY_SSL not found in .env file")
        print("\n📝 Please add to your .env file:")
        print("   VERIFY_SSL=false")
        sys.exit(1)
    
    if not OUTPUT_DIR:
        print("❌ Error: OUTPUT_DIR not found in .env file")
        print("\n📝 Please add to your .env file:")
        print("   OUTPUT_DIR=.")
        sys.exit(1)
    
    if not user_id:
        print("❌ Error: user_id is required")
        return None
    
    if not planning_period_id:
        print("❌ Error: planning_period_id is required")
        return None
    
    # Build endpoint - ensure base URL includes /api/v1
    base_url = OKR_BASE_URL.rstrip('/')
    # Ensure base URL ends with /api/v1
    if not base_url.endswith('/api/v1'):
        if base_url.endswith('/'):
            base_url = base_url.rstrip('/') + '/api/v1'
        else:
            base_url = base_url + '/api/v1'
    
    endpoint = f"/plan/find-all-plans/users/{user_id}/planning-period/{planning_period_id}"
    url = f"{base_url}{endpoint}"
    
    # Add query parameters if provided
    params = {}
    if for_plan:
        params['forPlan'] = for_plan
    
    # Setup headers (matching browser request format)
    headers = {
        'Authorization': f'Bearer {FIREBASE_TOKEN}',
        'tenantId': TENANT_ID,
        'tenantid': TENANT_ID,  # Some APIs use lowercase
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'createdby': user_id,
        'requestedby': user_id
    }
    
    # Use provided session_id or from env
    active_session_id = session_id or SESSION_ID
    if active_session_id:
        headers['sessionId'] = active_session_id
    
    print("📋 Fetching Someone's Daily Plans")
    print(f"📡 GET {url}")
    if params:
        print(f"🔍 Query params: {params}")
    print(f"👤 User ID: {user_id}")
    print(f"📅 Planning Period ID: {planning_period_id}")
    print(f"🔑 Tenant ID: {TENANT_ID}")
    print(f"⏱️  Timeout: {REQUEST_TIMEOUT}s")
    print(f"🔒 SSL Verify: {VERIFY_SSL}")
    if active_session_id:
        print(f"📅 Session ID: {active_session_id}")
    else:
        print("📅 Using active session")
    print("-" * 50)
    
    try:
        # Make request (SSL verification from .env)
        response = requests.get(
            url, 
            headers=headers, 
            params=params,
            timeout=REQUEST_TIMEOUT,
            verify=VERIFY_SSL
        )
        
        print(f"📊 Status: HTTP {response.status_code}")
        
        # Handle 304 Not Modified (cached response - still valid)
        if response.status_code == 304:
            print("⚠️  Response 304 Not Modified (cached)")
            print("   The server indicates the resource hasn't changed")
            print("   This usually means the request was successful but cached")
            # For 304, we might not get a body, so we'll treat it as an error
            # or you might want to use cached data if available
            print("   Note: 304 responses typically don't include response body")
            return None
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                # Check if response is encrypted and decrypt if needed
                if decryptor and isinstance(response_data, dict) and 'data' in response_data:
                    if isinstance(response_data['data'], str) and is_encrypted(response_data['data']):
                        print("   🔓 Response is encrypted, decrypting...")
                        try:
                            data = decryptor.decrypt_response(response_data['data'])
                            print("   ✅ Decrypted successfully!")
                        except Exception as decrypt_error:
                            print(f"   ❌ Decryption error: {decrypt_error}")
                            return None
                    else:
                        # Try decrypt_if_encrypted for nested encryption
                        data = decryptor.decrypt_if_encrypted(response_data) if decryptor else response_data
                elif decryptor:
                    # Check if the entire response is encrypted or has nested encrypted fields
                    data = decryptor.decrypt_if_encrypted(response_data)
                else:
                    data = response_data
                
                # Ensure data is in expected format (list or dict)
                if not isinstance(data, (list, dict)):
                    print(f"⚠️  Unexpected response format: {type(data).__name__}")
                    print(f"   Response: {str(data)[:200]}")
                    return None
                
                # Filter to only Daily plans and clean nested objects
                def clean_daily_plan(plan):
                    """Remove nested objects that are not Daily"""
                    if not isinstance(plan, dict):
                        return plan
                    
                    # Create a copy to avoid modifying original
                    cleaned = plan.copy()
                    
                    # Remove parentPlan if it's not Daily
                    if 'parentPlan' in cleaned and cleaned['parentPlan']:
                        parent_plan = cleaned['parentPlan']
                        if isinstance(parent_plan, dict) and parent_plan.get('description') != 'Daily':
                            cleaned['parentPlan'] = None
                    
                    # Clean nested plan array (child plans)
                    if 'plan' in cleaned and isinstance(cleaned['plan'], list):
                        cleaned['plan'] = [
                            clean_daily_plan(child_plan) 
                            for child_plan in cleaned['plan'] 
                            if isinstance(child_plan, dict) and child_plan.get('description') == 'Daily'
                        ]
                    
                    return cleaned
                
                def extract_plans_list(response_data, max_depth=5):
                    """Recursively extract list of plans from nested response structures"""
                    if max_depth <= 0:
                        print("   ⚠️  Max recursion depth reached")
                        return None
                    
                    if isinstance(response_data, list):
                        return response_data
                    
                    if isinstance(response_data, dict):
                        # Check common keys for lists
                        for key in ['items', 'data', 'plans', 'results']:
                            if key in response_data:
                                value = response_data[key]
                                if isinstance(value, list):
                                    print(f"   📦 Found list in '{key}' with {len(value)} items")
                                    return value
                                elif isinstance(value, str):
                                    # Check if it's encrypted (new format enc:v1: or old format iv:data)
                                    parts = value.split(':')
                                    is_old_format = len(parts) == 2 and len(parts[0]) >= 24 and all(c in '0123456789abcdefABCDEF' for c in parts[0])
                                    is_new_format = is_encrypted(value) if decryptor else False
                                    
                                    if is_new_format or is_old_format:
                                        format_type = 'new' if is_new_format else 'old'
                                        print(f"   🔓 '{key}' field is encrypted ({format_type} format), decrypting...")
                                        try:
                                            if is_new_format and decryptor:
                                                decrypted = decryptor.decrypt_response(value)
                                            elif is_old_format:
                                                decrypted = decrypt_old_format(value)
                                            else:
                                                print(f"   ⚠️  No decryptor available for {format_type} format")
                                                continue
                                            print(f"   ✅ Decrypted, type: {type(decrypted).__name__}")
                                            # Recursively process decrypted data
                                            result = extract_plans_list(decrypted, max_depth - 1)
                                            if result is not None:
                                                return result
                                        except Exception as e:
                                            print(f"   ❌ Decryption error: {e}")
                                            import traceback
                                            traceback.print_exc()
                                elif isinstance(value, dict):
                                    # Recursively check nested dict
                                    result = extract_plans_list(value, max_depth - 1)
                                    if result is not None:
                                        return result
                        
                        # Check if it's a single plan object
                        if 'description' in response_data:
                            return [response_data] if response_data.get('description') == 'Daily' else []
                        
                        # Try to find any list in the dict
                        for key, value in response_data.items():
                            if isinstance(value, list):
                                print(f"   📦 Found list in '{key}' with {len(value)} items")
                                return value
                            elif isinstance(value, dict):
                                result = extract_plans_list(value, max_depth - 1)
                                if result is not None:
                                    return result
                    
                    return None
                
                # Extract plans list from response (handles nested structures)
                plans_list = extract_plans_list(data)
                
                if plans_list is None:
                    print(f"⚠️  Could not extract plans list from response")
                    print(f"   Response type: {type(data).__name__}")
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())[:10]}")
                        print(f"   Sample: {str(data)[:300]}")
                    data = []
                elif isinstance(plans_list, list):
                    all_plans = plans_list
                    # Filter to only Daily plans
                    daily_plans = [
                        plan for plan in all_plans 
                        if isinstance(plan, dict) and plan.get('description') == 'Daily'
                    ]
                    # Clean nested objects from Daily plans
                    daily_plans = [clean_daily_plan(plan) for plan in daily_plans]
                    data = daily_plans
                    print(f"✅ Success! Retrieved {len(all_plans)} total plans")
                    print(f"📅 Filtered to {len(daily_plans)} Daily plans")
                    print(f"🧹 Cleaned nested non-Daily objects (parentPlan, etc.)")
                else:
                    data = []
                
                
                print(f"📦 Daily plans count: {len(data) if isinstance(data, list) else 'N/A'}")
                
                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"someone_daily_plans_{user_id}_{timestamp}.json"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                # Ensure output directory exists
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"💾 Saved to: {filepath}")
                
                return data
            except json.JSONDecodeError:
                print("⚠️  Response is not JSON, saving as text")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"someone_daily_plans_{user_id}_{timestamp}.txt"
                filepath = os.path.join(OUTPUT_DIR, filename)
                
                # Ensure output directory exists
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                
                with open(filepath, 'w') as f:
                    f.write(response.text)
                print(f"💾 Saved to: {filepath}")
                return {"text": response.text}
        elif response.status_code == 404:
            print(f"❌ Error 404: Endpoint not found")
            print(f"   URL: {url}")
            print(f"   Response: {response.text}")
            print("\n💡 Try checking:")
            print("   1. Is the base URL correct?")
            print("   2. Is the endpoint path correct?")
            print("   3. Are the userId and planningPeriodId valid?")
            print("   4. Check if the API server is running")
            return None
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Traceback:")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fetch someone\'s daily plans from OKR backend',
        epilog='Example: python3 api.py --user-id abc123 --planning-period-id xyz789\n'
               'Or set USER_ID and PLANNING_PERIOD_ID in .env file to run without arguments.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--user-id', 
        type=str, 
        default=DEFAULT_USER_ID,
        help='User ID (required, can be set in .env as USER_ID)'
    )
    parser.add_argument(
        '--planning-period-id', 
        type=str, 
        default=DEFAULT_PLANNING_PERIOD_ID,
        help='Planning period ID (required, can be set in .env as PLANNING_PERIOD_ID)'
    )
    parser.add_argument(
        '--for-plan', 
        type=str, 
        default=DEFAULT_FOR_PLAN,
        help='Optional forPlan query parameter (can be set in .env as FOR_PLAN)'
    )
    parser.add_argument(
        '--session-id', 
        type=str, 
        help='Optional session ID (uses SESSION_ID from .env if not provided)'
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.user_id:
        print("❌ Error: --user-id is required")
        print("   You can either:")
        print("   1. Pass it as argument: --user-id <userId>")
        print("   2. Set it in .env file: USER_ID=<userId>")
        sys.exit(1)
    
    if not args.planning_period_id:
        print("❌ Error: --planning-period-id is required")
        print("   You can either:")
        print("   1. Pass it as argument: --planning-period-id <planningPeriodId>")
        print("   2. Set it in .env file: PLANNING_PERIOD_ID=<planningPeriodId>")
        sys.exit(1)
    
    result = get_someone_daily_plans(
        args.user_id,
        args.planning_period_id,
        for_plan=args.for_plan,
        session_id=args.session_id
    )
    
    if result:
        print("\n✅ Script completed successfully")
    else:
        print("\n❌ Script failed")
        sys.exit(1)
