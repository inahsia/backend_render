"""
Quick test script to verify player creation is working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Player, Booking, CustomUser
from django.db import transaction

# Check current state
print("\n=== CURRENT STATE ===")
print(f"Total Players: {Player.objects.count()}")
print(f"Total Users: {CustomUser.objects.count()}")
print(f"Total Bookings: {Booking.objects.count()}")

# Show recent players
recent_players = Player.objects.order_by('-id')[:5]
print("\n=== RECENT PLAYERS ===")
for p in recent_players:
    print(f"ID: {p.id}, Name: {p.name}, Email: {p.email}, Booking: {p.booking_id}")

# Show recent bookings
recent_bookings = Booking.objects.order_by('-id')[:5]
print("\n=== RECENT BOOKINGS ===")
for b in recent_bookings:
    print(f"ID: {b.id}, User: {b.user.email}, Status: {b.status}, Players: {b.players.count()}")

# Test creating a player for the first available paid booking
try:
    test_booking = Booking.objects.filter(status='confirmed').first()
    if test_booking:
        print(f"\n=== TESTING PLAYER CREATION ===")
        print(f"Using Booking ID: {test_booking.id}")
        
        test_player = Player.objects.create(
            booking=test_booking,
            name="Test Player",
            email=f"testplayer_{Player.objects.count() + 1}@test.com",
            phone="1234567890"
        )
        print(f"✓ Player created successfully: ID={test_player.id}")
        print(f"✓ Has user account: {test_player.user is not None}")
        print(f"✓ Has QR code: {bool(test_player.qr_code)}")
        
        # Clean up test player
        test_player.delete()
        print("✓ Test player cleaned up")
    else:
        print("\n⚠️ No confirmed bookings found to test with")
except Exception as e:
    print(f"\n❌ Error creating player: {e}")
    import traceback
    traceback.print_exc()
