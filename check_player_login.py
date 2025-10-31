"""
Check player accounts and login credentials
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from core.models import Player, CustomUser, UserProfile

print("\n=== PLAYER ACCOUNTS CHECK ===")
print(f"Total Players: {Player.objects.count()}")
print(f"Total Users: {CustomUser.objects.count()}")

print("\n=== RECENT PLAYERS ===")
players = Player.objects.all().order_by('-id')[:10]
for p in players:
    print(f"\nPlayer ID: {p.id}")
    print(f"  Name: {p.name}")
    print(f"  Email: {p.email}")
    print(f"  Has User: {p.user is not None}")
    if p.user:
        print(f"  User Email: {p.user.email}")
        print(f"  User Active: {p.user.is_active}")
        profile = getattr(p.user, 'profile', None)
        if profile:
            print(f"  User Type: {profile.user_type}")
        else:
            print(f"  No Profile!")
    else:
        print(f"  NO USER ACCOUNT LINKED!")

print("\n=== USERS WITH PLAYER TYPE ===")
player_profiles = UserProfile.objects.filter(user_type='player')[:5]
for profile in player_profiles:
    print(f"\nUser: {profile.user.email}")
    print(f"  Active: {profile.user.is_active}")
    print(f"  Has Password: {bool(profile.user.password)}")
    print(f"  Player Record: {Player.objects.filter(user=profile.user).exists()}")

# Test login for a player
print("\n=== TEST PLAYER LOGIN ===")
if players.exists():
    test_player = players.first()
    print(f"Testing login for: {test_player.email}")
    
    if test_player.user:
        # Check if password is "redball"
        from django.contrib.auth import authenticate
        user = authenticate(username=test_player.user.email, password='redball')
        if user:
            print("✅ Login with 'redball' works!")
        else:
            print("❌ Login with 'redball' FAILED!")
            print("Trying to reset password...")
            test_player.user.set_password('redball')
            test_player.user.save()
            user = authenticate(username=test_player.user.email, password='redball')
            if user:
                print("✅ Password reset successful, login now works!")
            else:
                print("❌ Still failing after reset")
    else:
        print("❌ No user account linked to this player!")
