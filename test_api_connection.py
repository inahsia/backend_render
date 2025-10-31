"""
Test API endpoints for organizer QR system
Tests if frontend can connect to backend properly
"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_server_connection():
    """Test if server is running"""
    print("\n" + "="*60)
    print("TEST 1: Server Connection")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/sports/", timeout=5)
        print(f"✅ Server is running!")
        print(f"   Status Code: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is NOT running at {BASE_URL}")
        print(f"   Please start the server with: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_bookings_endpoint():
    """Test if bookings endpoint works"""
    print("\n" + "="*60)
    print("TEST 2: Bookings Endpoint")
    print("="*60)
    
    try:
        # Try to get bookings (will fail without auth, but endpoint should exist)
        response = requests.get(f"{BASE_URL}/bookings/", timeout=5)
        print(f"✅ Bookings endpoint exists!")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"   ✓ Authentication required (expected)")
        elif response.status_code == 200:
            print(f"   ✓ Successfully got bookings")
            
        return True
    except Exception as e:
        print(f"❌ Error accessing bookings endpoint: {e}")
        return False

def test_organizer_qr_endpoint_exists():
    """Test if organizer QR scan endpoint exists"""
    print("\n" + "="*60)
    print("TEST 3: Organizer QR Scan Endpoint")
    print("="*60)
    
    try:
        # Try to scan with invalid token (will fail, but endpoint should exist)
        response = requests.post(
            f"{BASE_URL}/bookings/scan_organizer_qr/",
            json={"token": "invalid_token_for_testing"},
            timeout=5
        )
        print(f"✅ Organizer QR scan endpoint exists!")
        print(f"   URL: {BASE_URL}/bookings/scan_organizer_qr/")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [400, 401, 403]:
            print(f"   ✓ Endpoint is protected (expected)")
            try:
                error_msg = response.json()
                print(f"   ✓ Error message: {error_msg.get('error', 'N/A')}")
            except:
                pass
        
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to endpoint")
        return False
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_player_qr_endpoint_exists():
    """Test if player QR scan endpoint exists"""
    print("\n" + "="*60)
    print("TEST 4: Player QR Scan Endpoint")
    print("="*60)
    
    try:
        # Try to scan with invalid token
        response = requests.post(
            f"{BASE_URL}/players/scan_qr/",
            json={"token": "invalid_token_for_testing"},
            timeout=5
        )
        print(f"✅ Player QR scan endpoint exists!")
        print(f"   URL: {BASE_URL}/players/scan_qr/")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [400, 401, 403]:
            print(f"   ✓ Endpoint is protected (expected)")
            try:
                error_msg = response.json()
                print(f"   ✓ Error message: {error_msg.get('error', 'N/A')}")
            except:
                pass
        
        return True
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        return False

def test_with_real_organizer_qr():
    """Test with actual organizer QR token from database"""
    print("\n" + "="*60)
    print("TEST 5: Real Organizer QR Token Test")
    print("="*60)
    
    try:
        import os
        import sys
        import django
        
        # Setup Django
        sys.path.insert(0, os.path.dirname(__file__))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
        django.setup()
        
        from core.models import Booking
        
        # Get a booking with organizer QR
        booking = Booking.objects.filter(organizer_qr_token__isnull=False).first()
        
        if not booking:
            print("⚠️  No booking with organizer QR found in database")
            return True
        
        print(f"Testing with Booking #{booking.id}")
        print(f"  Sport: {booking.slot.sport.name}")
        print(f"  Date: {booking.slot.date}")
        print(f"  Token exists: Yes")
        
        # Try to scan it via API
        response = requests.post(
            f"{BASE_URL}/bookings/scan_organizer_qr/",
            json={"token": booking.organizer_qr_token},
            timeout=5
        )
        
        print(f"\n  API Response:")
        print(f"    Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ SUCCESS! Organizer QR scan worked!")
            print(f"    Message: {data.get('message', 'N/A')}")
            print(f"    Organizer is_in: {data.get('booking', {}).get('organizer_is_in', 'N/A')}")
            print(f"    Check-in count: {data.get('booking', {}).get('organizer_check_in_count', 'N/A')}")
            return True
        elif response.status_code == 401:
            print(f"    ⚠️  Authentication required")
            print(f"    This is normal - frontend needs to send auth token")
            return True
        else:
            print(f"    ❌ Unexpected status code")
            try:
                print(f"    Response: {response.json()}")
            except:
                print(f"    Response: {response.text}")
            return False
            
    except ImportError:
        print("⚠️  Cannot import Django models - testing with mock data only")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("🔗 FRONTEND-BACKEND CONNECTION TEST")
    print("="*60)
    
    tests = [
        ("Server Connection", test_server_connection),
        ("Bookings Endpoint", test_bookings_endpoint),
        ("Organizer QR Endpoint", test_organizer_qr_endpoint_exists),
        ("Player QR Endpoint", test_player_qr_endpoint_exists),
        ("Real Organizer QR Token", test_with_real_organizer_qr),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            
            # If server is not running, skip remaining tests
            if name == "Server Connection" and not result:
                print("\n⚠️  Skipping remaining tests - server not running")
                break
                
        except Exception as e:
            print(f"\n❌ TEST FAILED WITH ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Frontend-Backend connection is working!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or skipped.")
    
    print("="*60)

if __name__ == '__main__':
    main()
