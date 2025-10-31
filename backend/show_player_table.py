import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, data_type, character_maximum_length 
    FROM information_schema.columns 
    WHERE table_name='core_player' 
    ORDER BY ordinal_position
""")

print("\n" + "="*70)
print("TABLE: core_player (Player Model)")
print("="*70)
print(f"{'COLUMN NAME':<30} {'DATA TYPE':<20} {'MAX LENGTH':<15}")
print("-"*70)

for row in cursor.fetchall():
    col_name = row[0]
    data_type = row[1]
    max_length = row[2] if row[2] else '-'
    print(f"{col_name:<30} {data_type:<20} {max_length:<15}")

print("\n" + "="*70)
print("QR-RELATED COLUMNS:")
print("="*70)
print("  • qr_token  - Signed token string for QR code")
print("  • qr_code   - Path to QR code image file (PNG)")
print("  • is_in     - Boolean: Player currently checked in?")
print("  • check_in_count - Number of check-ins (0, 1, or 2)")
print("  • last_check_in  - Timestamp of last check-in")
print("  • last_check_out - Timestamp of last check-out")
print("="*70 + "\n")

# Show sample player data
from core.models import Player
player = Player.objects.first()
if player:
    print("\nSAMPLE PLAYER DATA:")
    print("="*70)
    print(f"ID: {player.id}")
    print(f"Name: {player.name}")
    print(f"Email: {player.email}")
    print(f"QR Token: {player.qr_token[:80]}..." if player.qr_token else "None")
    print(f"QR Image: {player.qr_code}")
    print(f"Is In: {player.is_in}")
    print(f"Check-in Count: {player.check_in_count}")
    print(f"Booking ID: {player.booking_id}")
    print("="*70)
