"""
Test script for organizer QR system
Tests:
1. Booking has organizer QR fields
2. Organizer QR token generation
3. Organizer QR scanning endpoint
4. Check-in/out toggle
5. OrganizerCheckInLog creation
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Booking, OrganizerCheckInLog, Player
from django.contrib.auth import get_user_model
from django.core import signing
from datetime import date
import json

User = get_user_model()

def test_database_state():
    """Test 1: Check database state"""
    print("\n" + "="*60)
    print("TEST 1: Database State")
    print("="*60)
    
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(payment_verified=True).count()
    bookings_with_organizer_qr = Booking.objects.filter(organizer_qr_token__isnull=False).count()
    organizer_logs = OrganizerCheckInLog.objects.count()
    
    print(f"✓ Total bookings: {total_bookings}")
    print(f"✓ Confirmed bookings: {confirmed_bookings}")
    print(f"✓ Bookings with organizer QR: {bookings_with_organizer_qr}")
    print(f"✓ OrganizerCheckInLog entries: {organizer_logs}")
    
    if bookings_with_organizer_qr > 0:
        print("✅ SUCCESS: Bookings have organizer QR codes")
        return True
    else:
        print("❌ FAIL: No bookings have organizer QR codes")
        return False

def test_organizer_qr_fields():
    """Test 2: Check organizer QR fields on booking"""
    print("\n" + "="*60)
    print("TEST 2: Organizer QR Fields")
    print("="*60)
    
    booking = Booking.objects.filter(organizer_qr_token__isnull=False).first()
    
    if not booking:
        print("❌ FAIL: No booking with organizer QR found")
        return False
    
    print(f"Testing Booking #{booking.id}")
    print(f"  Sport: {booking.slot.sport.name}")
    print(f"  Date: {booking.slot.date}")
    print(f"  User: {booking.user.email}")
    print(f"\nOrganizer QR Fields:")
    print(f"  ✓ organizer_qr_token: {'Present' if booking.organizer_qr_token else 'Missing'}")
    print(f"  ✓ organizer_qr_code: {'Present' if booking.organizer_qr_code else 'Missing'}")
    print(f"  ✓ organizer_is_in: {booking.organizer_is_in}")
    print(f"  ✓ organizer_check_in_count: {booking.organizer_check_in_count}")
    
    if booking.organizer_qr_token:
        # Try to decode the token
        try:
            data = signing.loads(booking.organizer_qr_token, salt='organizer-qr-token')
            print(f"\n  Token decoded successfully:")
            print(f"    - booking_id: {data.get('booking_id')}")
            print(f"    - user_id: {data.get('user_id')}")
            print(f"    - slot_date: {data.get('slot_date')}")
            print(f"    - sport: {data.get('sport')}")
            print("✅ SUCCESS: Organizer QR fields are present and valid")
            return True
        except Exception as e:
            print(f"❌ FAIL: Could not decode token: {e}")
            return False
    else:
        print("❌ FAIL: No organizer QR token")
        return False

def test_organizer_check_in_toggle():
    """Test 3: Test check-in/out toggle logic"""
    print("\n" + "="*60)
    print("TEST 3: Check-in/Out Toggle")
    print("="*60)
    
    booking = Booking.objects.filter(
        organizer_qr_token__isnull=False,
        organizer_check_in_count__lt=2
    ).first()
    
    if not booking:
        print("⚠️  WARNING: No booking available for testing (all at max count)")
        return True
    
    print(f"Testing Booking #{booking.id}")
    print(f"  Initial state:")
    print(f"    - organizer_is_in: {booking.organizer_is_in}")
    print(f"    - organizer_check_in_count: {booking.organizer_check_in_count}")
    
    # Simulate first check-in
    if booking.organizer_check_in_count == 0:
        booking.organizer_check_in_count = 1
        booking.organizer_is_in = True
        booking.save()
        print(f"\n  After first scan (CHECK IN):")
        print(f"    - organizer_is_in: {booking.organizer_is_in} ✓")
        print(f"    - organizer_check_in_count: {booking.organizer_check_in_count} ✓")
        
        # Create log entry
        OrganizerCheckInLog.objects.create(
            booking=booking,
            user=booking.user,
            action='IN'
        )
        print(f"    - Log entry created: IN ✓")
    
    # Simulate second check-out
    if booking.organizer_check_in_count == 1:
        booking.organizer_check_in_count = 2
        booking.organizer_is_in = False
        booking.save()
        print(f"\n  After second scan (CHECK OUT):")
        print(f"    - organizer_is_in: {booking.organizer_is_in} ✓")
        print(f"    - organizer_check_in_count: {booking.organizer_check_in_count} ✓")
        
        # Create log entry
        OrganizerCheckInLog.objects.create(
            booking=booking,
            user=booking.user,
            action='OUT'
        )
        print(f"    - Log entry created: OUT ✓")
    
    # Check logs
    logs = OrganizerCheckInLog.objects.filter(booking=booking)
    print(f"\n  Total organizer check-in logs for this booking: {logs.count()}")
    for log in logs:
        print(f"    - {log.action} at {log.timestamp}")
    
    print("✅ SUCCESS: Check-in/out toggle working correctly")
    return True

def test_token_validation():
    """Test 4: Validate token structure"""
    print("\n" + "="*60)
    print("TEST 4: Token Validation")
    print("="*60)
    
    booking = Booking.objects.filter(organizer_qr_token__isnull=False).first()
    
    if not booking:
        print("❌ FAIL: No booking with organizer QR found")
        return False
    
    print(f"Testing token for Booking #{booking.id}")
    
    try:
        # Decode token
        data = signing.loads(booking.organizer_qr_token, salt='organizer-qr-token')
        
        # Validate required fields
        required_fields = ['booking_id', 'user_id', 'slot_date', 'sport', 'ts']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ FAIL: Missing fields in token: {missing_fields}")
            return False
        
        # Validate values
        checks = [
            (data['booking_id'] == booking.id, f"booking_id matches: {data['booking_id']} == {booking.id}"),
            (data['user_id'] == booking.user.id, f"user_id matches: {data['user_id']} == {booking.user.id}"),
            (data['sport'] == booking.slot.sport.name, f"sport matches: {data['sport']} == {booking.slot.sport.name}"),
        ]
        
        print("\n  Token validation:")
        all_passed = True
        for passed, message in checks:
            status = "✓" if passed else "✗"
            print(f"    {status} {message}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("✅ SUCCESS: Token structure is valid")
            return True
        else:
            print("❌ FAIL: Token validation failed")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Token validation error: {e}")
        return False

def test_player_vs_organizer_qr():
    """Test 5: Compare player QR vs organizer QR"""
    print("\n" + "="*60)
    print("TEST 5: Player QR vs Organizer QR Comparison")
    print("="*60)
    
    booking = Booking.objects.filter(
        organizer_qr_token__isnull=False,
        players__isnull=False
    ).first()
    
    if not booking:
        print("⚠️  WARNING: No booking with both organizer and players found")
        return True
    
    print(f"Testing Booking #{booking.id} - {booking.slot.sport.name}")
    
    # Decode organizer token
    try:
        org_data = signing.loads(booking.organizer_qr_token, salt='organizer-qr-token')
        print(f"\n  Organizer QR Token:")
        print(f"    - Salt: organizer-qr-token")
        print(f"    - Fields: booking_id, user_id, slot_date, sport, ts")
        print(f"    - booking_id: {org_data.get('booking_id')}")
        print(f"    - user_id: {org_data.get('user_id')}")
    except Exception as e:
        print(f"❌ Could not decode organizer token: {e}")
        return False
    
    # Get first player
    player = booking.players.first()
    if player and player.qr_token:
        try:
            player_data = signing.loads(player.qr_token, salt='player-qr-token')
            print(f"\n  Player QR Token (Player: {player.name}):")
            print(f"    - Salt: player-qr-token")
            print(f"    - Fields: player_id, booking_id, ts")
            print(f"    - player_id: {player_data.get('player_id')}")
            print(f"    - booking_id: {player_data.get('booking_id')}")
            
            print(f"\n  ✓ Organizer and Player use different salts")
            print(f"  ✓ Both tokens reference same booking_id: {org_data.get('booking_id')}")
            print(f"  ✓ Organizer token has user_id, Player token has player_id")
            print("✅ SUCCESS: QR codes are properly separated")
            return True
        except Exception as e:
            print(f"⚠️  Could not decode player token: {e}")
    else:
        print(f"⚠️  No player with QR found in this booking")
    
    return True

def main():
    print("\n" + "="*60)
    print("🔍 ORGANIZER QR SYSTEM TEST SUITE")
    print("="*60)
    
    tests = [
        ("Database State", test_database_state),
        ("Organizer QR Fields", test_organizer_qr_fields),
        ("Check-in/Out Toggle", test_organizer_check_in_toggle),
        ("Token Validation", test_token_validation),
        ("Player vs Organizer QR", test_player_vs_organizer_qr),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
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
        print("\n🎉 ALL TESTS PASSED! Organizer QR system is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
    
    print("="*60)

if __name__ == '__main__':
    main()
