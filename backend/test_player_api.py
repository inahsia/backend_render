"""
Test the /api/players/me/ endpoint
"""
import requests
import json

# Login as player
print("=" * 60)
print("TESTING PLAYER API ENDPOINT")
print("=" * 60)

# Step 1: Login
print("\n1. Logging in as player...")
login_url = "http://localhost:8000/api/auth/jwt_login/"
login_data = {
    "email": "me@gmail.com",
    "password": "redball"
}

try:
    response = requests.post(login_url, json=login_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Login successful!")
        print(f"   User: {data.get('user', {}).get('email')}")
        print(f"   User Type: {data.get('user', {}).get('user_type')}")
        token = data.get('access')
        print(f"   Token: {token[:50]}..." if token else "   ❌ No token!")
        
        if not token:
            print("\n❌ No access token returned!")
            exit(1)
        
        # Step 2: Call /api/players/me/
        print("\n2. Calling /api/players/me/...")
        me_url = "http://localhost:8000/api/players/me/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        me_response = requests.get(me_url, headers=headers)
        print(f"   Status: {me_response.status_code}")
        
        if me_response.status_code == 200:
            player_data = me_response.json()
            print(f"   ✓ Player data retrieved!")
            print(f"\n   Player Info:")
            print(f"     ID: {player_data.get('id')}")
            print(f"     Name: {player_data.get('name')}")
            print(f"     Email: {player_data.get('email')}")
            print(f"     Is In: {player_data.get('is_in')}")
            print(f"     Has QR Token: {bool(player_data.get('qr_token'))}")
            print(f"     QR Token Preview: {player_data.get('qr_token', '')[:50]}...")
            print(f"     Has QR URL: {bool(player_data.get('qr_code_url'))}")
            
            if player_data.get('booking_details'):
                bd = player_data['booking_details']
                print(f"\n   Booking Details:")
                print(f"     Sport: {bd.get('sport')}")
                print(f"     Date: {bd.get('slot_date')}")
                print(f"     Time: {bd.get('start_time')} - {bd.get('end_time')}")
            
            print("\n✅ API ENDPOINT WORKING CORRECTLY!")
        else:
            print(f"   ❌ Failed to get player data")
            print(f"   Response: {me_response.text}")
    else:
        print(f"   ❌ Login failed!")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
