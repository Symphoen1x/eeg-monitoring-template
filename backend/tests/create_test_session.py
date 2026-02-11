"""
Helper Script: Create Session for Face Detection Testing
Logs in and creates a test session, then prints the session ID
"""

import requests
import sys

BASE_URL = "http://localhost:8000"

# Update these with your login credentials
EMAIL = "test123@gmail.com"  # Change to your registered email
PASSWORD = "12345678"  # Change to your password

def login():
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json={"email": EMAIL, "password": PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    tokens = response.json()
    return tokens['access_token']

def create_session(token):
    """Create a test session"""
    response = requests.post(
        f"{BASE_URL}/api/v1/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_name": "Test Face Detection",
            "device_type": "Mock MediaPipe",
            "settings": {}
        }
    )
    
    if response.status_code != 201:  # 201 Created is success
        print(f"❌ Create session failed: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    session = response.json()
    return session['id']

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Session Creator for Face Detection Testing")
    print("=" * 60)
    print()
    
    print("📝 Logging in...")
    token = login()
    print("   ✅ Login successful!")
    
    print()
    print("📝 Creating session...")
    session_id = create_session(token)
    print("   ✅ Session created!")
    
    print()
    print("=" * 60)
    print("🆔 SESSION ID:")
    print(f"   {session_id}")
    print("=" * 60)
    print()
    print("📝 Next steps:")
    print(f"   1. Copy this ID: {session_id}")
    print("   2. Edit mock_face_sender.py")
    print(f"   3. Change SESSION_ID to: \"{session_id}\"")
    print("   4. Run: python mock_face_sender.py")
    print()
