"""
Fix Missing QR Tokens
Generates QR tokens for all players that don't have them
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Player

print("=" * 60)
print("FIXING MISSING QR TOKENS")
print("=" * 60)

# Find players without QR tokens
players_without_qr = Player.objects.filter(qr_token__isnull=True) | Player.objects.filter(qr_token='')
total = players_without_qr.count()

print(f"\nFound {total} players without QR tokens\n")

if total == 0:
    print("✓ All players already have QR tokens!")
else:
    success_count = 0
    fail_count = 0
    
    for player in players_without_qr:
        try:
            print(f"Generating QR for Player #{player.id}: {player.name}...", end=" ")
            player.generate_qr_code()
            player.save(update_fields=['qr_token', 'qr_code'])
            print("✓ Success")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed: {e}")
            fail_count += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS:")
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Failed: {fail_count}")
    print("=" * 60)

# Verify all players now have QR tokens
remaining = Player.objects.filter(qr_token__isnull=True).count() + Player.objects.filter(qr_token='').count()
print(f"\nPlayers without QR tokens: {remaining}")

if remaining == 0:
    print("🎉 All players now have QR tokens!")
else:
    print(f"⚠️ {remaining} players still missing QR tokens")
