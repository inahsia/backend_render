import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Player

print("\n" + "="*70)
print("PLAYER QR DATA")
print("="*70)

for player in Player.objects.all():
    print(f"ID: {player.id}")
    print(f"Name: {player.name}")
    print(f"Email: {player.email}")
    print(f"QR Token: {player.qr_token[:80]}..." if player.qr_token else "None")
    print(f"QR Image: {player.qr_code}")
    print(f"Is In: {player.is_in}")
    print(f"Check-in Count: {player.check_in_count}")
    print(f"Booking ID: {player.booking_id}")
    print("-"*70)