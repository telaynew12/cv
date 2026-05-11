#!/usr/bin/env python3
"""
Decode Firebase Token Script
Reads FIREBASE_API_ID from .env, decodes the JWT token, and saves the information

Environment Variables (.env file):
    Required:
        FIREBASE_API_ID - Firebase authentication token
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# Configuration from .env
FIREBASE_ID_TOKEN = os.getenv("FIREBASE_API_ID")


def decode_jwt_token(token: str) -> dict:
    """
    Decode JWT token without verification to extract information
    
    Args:
        token: JWT token string
    
    Returns:
        Dictionary with decoded token information
    """
    try:
        # JWT tokens have 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT token format"}
        
        # Decode header and payload (they are base64url encoded)
        # Add padding if needed for base64 decoding
        header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
        payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
        
        header = json.loads(base64.urlsafe_b64decode(header_padded))
        payload = json.loads(base64.urlsafe_b64decode(payload_padded))
        
        # Extract useful information
        token_info = {
            "header": header,
            "payload": payload,
            "user_id": payload.get("user_id") or payload.get("sub") or payload.get("uid"),
            "email": payload.get("email"),
            "tenant_id": payload.get("name") or payload.get("tenant_id") or payload.get("tenantId"),
            "issued_at": datetime.fromtimestamp(payload.get("iat", 0)).isoformat() if payload.get("iat") else None,
            "expires_at": datetime.fromtimestamp(payload.get("exp", 0)).isoformat() if payload.get("exp") else None,
            "issuer": payload.get("iss"),
            "audience": payload.get("aud"),
            "firebase": payload.get("firebase", {}),
        }
        
        return token_info
    except Exception as e:
        return {"error": f"Failed to decode token: {str(e)}"}


def decode_and_save_token_info() -> dict:
    """
    Decode the Firebase token from .env and save the information
    
    Returns:
        Dictionary with decoded token information
    """
    if not FIREBASE_ID_TOKEN:
        print("❌ Error: FIREBASE_API_ID not found in .env file")
        return {"error": "FIREBASE_API_ID not found"}
    
    print(f"{'='*80}\n🔐 DECODING FIREBASE TOKEN\n{'='*80}\n")
    print(f"Token length: {len(FIREBASE_ID_TOKEN)} characters\n")
    
    # Decode the token
    token_info = decode_jwt_token(FIREBASE_ID_TOKEN)
    
    if "error" in token_info:
        print(f"❌ Error: {token_info['error']}\n")
        return token_info
    
    # Display decoded information
    print("📋 DECODED TOKEN INFORMATION:\n")
    print(f"  User ID: {token_info.get('user_id', 'N/A')}")
    print(f"  Email: {token_info.get('email', 'N/A')}")
    print(f"  Tenant ID: {token_info.get('tenant_id', 'N/A')}")
    print(f"  Issuer: {token_info.get('issuer', 'N/A')}")
    print(f"  Audience: {token_info.get('audience', 'N/A')}")
    print(f"  Issued At: {token_info.get('issued_at', 'N/A')}")
    print(f"  Expires At: {token_info.get('expires_at', 'N/A')}")
    
    # Check if token is expired
    if token_info.get('expires_at'):
        try:
            exp_timestamp = token_info['payload'].get('exp', 0)
            if exp_timestamp > 0:
                exp_time = datetime.fromtimestamp(exp_timestamp)
                now = datetime.now()
                if exp_time < now:
                    print(f"\n  ⚠️  WARNING: Token expired on {exp_time.isoformat()}")
                else:
                    print(f"\n  ✅ Token is valid until {exp_time.isoformat()}")
        except:
            pass
    
    # Save to file
    output_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"decoded_token_info_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(token_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved decoded token info to: {filepath}\n")
    token_info['saved_to'] = filepath
    
    return token_info


def main():
    """Main function - decode token and save information"""
    # Validate configuration
    if not FIREBASE_ID_TOKEN:
        print("❌ Error: FIREBASE_API_ID not found in .env file")
        print("   Please set FIREBASE_API_ID in your .env file")
        return
    
    # Decode and save token information
    token_info = decode_and_save_token_info()
    
    if "error" not in token_info:
        print("✅ Token decoded and saved successfully!\n")
    else:
        print("❌ Failed to decode token.\n")


if __name__ == "__main__":
    main()
