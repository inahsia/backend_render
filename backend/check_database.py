"""
Check database state for players and users
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Player, CustomUser, Booking

print('=== DATABASE STATE ===')
print(f'Total Players: {Player.objects.count()}')
print(f'Total Users: {CustomUser.objects.count()}')
print(f'Total Bookings: {Booking.objects.count()}')

print('\n=== RECENT PLAYERS ===')
for p in Player.objects.order_by('-id')[:5]:
    print(f'ID: {p.id}')
    print(f'  Name: {p.name}')
    print(f'  Email: {p.email}')
    print(f'  Has User: {p.user is not None}')
    if p.user:
        print(f'  User Email: {p.user.email}')
        print(f'  User Type: {p.user.profile.user_type if hasattr(p.user, "profile") else "No Profile"}')
    print(f'  Booking ID: {p.booking_id}')
    print()

print('\n=== RECENT BOOKINGS ===')
for b in Booking.objects.order_by('-id')[:3]:
    print(f'ID: {b.id}')
    print(f'  User: {b.user.email}')
    print(f'  Status: {b.status}')
    print(f'  Payment Verified: {b.payment_verified}')
    print(f'  Players Count: {b.players.count()}')
    print(f'  Created: {b.created_at}')
    print()

print('\n=== PLAYER USERS ===')
player_users = CustomUser.objects.filter(profile__user_type='player')
print(f'Total Player Users: {player_users.count()}')
for u in player_users[:5]:
    print(f'Email: {u.email}, Has Profile: {hasattr(u, "profile")}')
