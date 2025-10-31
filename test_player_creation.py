"""
Test script to verify player creation is working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Player, Booking, CustomUser, UserProfile
from django.db import transaction

print("\n=== CURRENT STATE ===")
print(f"Total Players: {Player.objects.count()}")
print(f"Total Users: {CustomUser.objects.count()}")
print(f"Total Bookings: {Booking.objects.count()}")

# Show recent players
print("\n=== RECENT 5 PLAYERS ===")
for p in Player.objects.order_by('-id')[:5]:
    print(f"ID: {p.id}, Name: {p.name}, Email: {p.email}, User: {p.user.email if p.user else 'NO USER'}")

# Find a confirmed booking to test with
print("\n=== AVAILABLE BOOKINGS FOR TESTING ===")
confirmed_bookings = Booking.objects.filter(payment_verified=True)[:3]
for b in confirmed_bookings:
    print(f"Booking #{b.id}, User: {b.user.email}, Sport: {b.slot.sport.name}, Players: {b.players.count()}")

if confirmed_bookings.exists():
    test_booking = confirmed_bookings.first()
    print(f"\n=== TESTING PLAYER CREATION ===")
    print(f"Using Booking #{test_booking.id}")
    
    # Test data
    test_email = f"test_player_{Player.objects.count() + 1}@test.com"
    
    try:
        with transaction.atomic():
            print(f"\nCreating player with email: {test_email}")
            
            # This should trigger the signal
            new_player = Player.objects.create(
                booking=test_booking,
                name="Test Player",
                email=test_email,
                phone="1234567890"
            )
            
            print(f"✓ Player created: ID={new_player.id}")
            print(f"✓ Has user: {new_player.user is not None}")
            
            if new_player.user:
                print(f"✓ User email: {new_player.user.email}")
                print(f"✓ User ID: {new_player.user.id}")
                
                # Check profile
                profile = UserProfile.objects.filter(user=new_player.user).first()
                if profile:
                    print(f"✓ Profile exists: user_type={profile.user_type}")
                else:
                    print("✗ No profile found!")
                    
                # Test login
                print(f"\n=== TESTING LOGIN ===")
                from django.contrib.auth import authenticate
                user = authenticate(username=test_email, password='redball')
                if user:
                    print(f"✓ Login successful with password 'redball'")
                else:
                    print(f"✗ Login failed!")
                    # Try to check password
                    if new_player.user.check_password('redball'):
                        print("  Password is correct but authenticate failed")
                    else:
                        print("  Password is NOT 'redball'")
            else:
                print("✗ Player has NO user account!")
                
            # Clean up test player
            print(f"\nCleaning up test player...")
            if new_player.user:
                new_player.user.delete()  # This will also delete the player
            else:
                new_player.delete()
            print("✓ Cleanup complete")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n⚠️ No confirmed bookings found to test with")
    print("Please create a booking and confirm payment first")

print("\n=== TEST COMPLETE ===")
