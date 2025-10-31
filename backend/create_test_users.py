"""
Create test users and sports data
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redball_academy.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Sport, UserProfile

User = get_user_model()

print("=" * 60)
print("Creating Test Data")
print("=" * 60)

# Create test user
test_users = [
    {'email': 'chigi@gmail.com', 'password': 'chigi123', 'first_name': 'Chigi', 'user_type': 'customer'},
    {'email': 'test@gmail.com', 'password': 'test123', 'first_name': 'Test', 'user_type': 'customer'},
]

for user_data in test_users:
    email = user_data['email']
    if User.objects.filter(email=email).exists():
        print(f"ℹ️  User {email} already exists")
    else:
        user = User.objects.create_user(
            email=email,
            password=user_data['password'],
            first_name=user_data['first_name']
        )
        # Create profile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'user_type': user_data['user_type']}
        )
        print(f"✅ Created user: {email} (password: {user_data['password']})")

# Create sports
sports = ['Cricket', 'Football', 'Tennis', 'Badminton']
for sport_name in sports:
    sport, created = Sport.objects.get_or_create(name=sport_name)
    if created:
        print(f"✅ Created sport: {sport_name}")
    else:
        print(f"ℹ️  Sport {sport_name} already exists")

print("=" * 60)
print("Done!")
print("=" * 60)
print("\nTest Users Created:")
for user_data in test_users:
    print(f"  Email: {user_data['email']}, Password: {user_data['password']}")
